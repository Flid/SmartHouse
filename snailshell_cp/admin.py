import json

from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import MultipleObjectsReturned
from django.utils.safestring import mark_safe
from fabric.api import execute

from snailshell_cp.clients.portainer import PortainerClient
from snailshell_cp.management.cluster_control import provision_slave_node
from snailshell_cp.management.cluster_control.base import (
    BaseClusterControlException,
    build_host_string
)
from snailshell_cp.management.cluster_control.utils import add_ssh_host
from snailshell_cp.models import AccessKey, DeployJob, Node, Service


def delete_node(modeladmin, request, queryset):
    try:
        node = queryset.get()
    except (MultipleObjectsReturned, Node.DoesNotExist):
        raise forms.ValidationError('Exactly one object has to be selected')

    if node.id == settings.ENV.PORTAINER_LOCAL_ENDPOINT_ID:
        raise forms.ValidationError('Can\'t remove the master node')

    portainer_client = PortainerClient.get_internal_client()
    portainer_client.remove_endpoint(node.id)

    # TODO show some message using https://docs.djangoproject.com/en/dev/ref/contrib/messages/
    node.delete()


delete_node.short_description = 'Detach node from the cluster'


class NodeCreateForm(forms.ModelForm):
    password = forms.CharField(
        max_length=255,
        help_text='Password is only used to add an ssh key and is never stored anywhere.',
    )

    reinstall_docker = forms.BooleanField(initial=True, required=False)

    class Meta:
        model = Node
        exclude = ['id', 'is_provisioned']

    def full_clean(self):
        super().full_clean()

        host_string = build_host_string(
            login=self.cleaned_data['login'],
            host=self.cleaned_data['host'],
            port=self.cleaned_data['port'],
        )

        try:
            add_ssh_host(
                name=self.cleaned_data['name'],
                login=self.cleaned_data['login'],
                password=self.cleaned_data['password'],
                host=self.cleaned_data['host'],
                port=self.cleaned_data['port'],
            )
            # Configure docker on the remote machine
            # and add an entrypoint to Portainer
            response = execute(
                provision_slave_node,
                name=self.cleaned_data['name'],
                host=host_string,
                hostname=self.cleaned_data['host'],
                reinstall_docker=self.cleaned_data.get('reinstall_docker', False),
            )

        except BaseClusterControlException as exc:
            self.add_error(None, str(exc))
            return

        self._obj_id = response[host_string]['entrypoint_id']

    def save(self, *args, **kwargs):
        self.instance.id = self._obj_id
        return super().save(*args, **kwargs)


class NodeAdmin(admin.ModelAdmin):
    def identifier(self, obj):
        client = PortainerClient.get_internal_client(auth=False)
        url = client.get_external_link_for_endpoint(obj.id)
        return mark_safe(f'<a href="{url}">{obj.id}</a>')

    actions = [delete_node]
    form = NodeCreateForm

    def get_actions(self, request):
        # Disable delete
        actions = super().get_actions(request)
        del actions['delete_selected']
        return actions

    list_display = (
        'identifier',
        'name',
        'host',
        'port',
    )


class ServiceForm(forms.ModelForm):
    def full_clean(self):
        super().full_clean()

        if self.instance is None:
            return

        for key in ['env_variables', 'host_config', 'volumes', 'command']:
            value = getattr(self.instance, key)

            if not value:
                continue

            try:
                value = json.loads(value)
            except ValueError:
                self.add_error(key, 'Invalid JSON')
                continue

            # Make it pretty
            setattr(self.instance, key, json.dumps(value, indent=2))

    class Meta:
        model = Service
        exclude = ['id', 'is_system_service']


class ServiceAdmin(admin.ModelAdmin):
    form = ServiceForm

    def node_name(self, obj):
        client = PortainerClient.get_internal_client(auth=False)
        url = client.get_external_link_for_endpoint(obj.node.id)
        return mark_safe(f'<a href="{url}">{obj.container_name}</a>')

    list_display = (
        'container_name',
        'image_name',
        'node_name',
    )


class AccessKeyAdmin(admin.ModelAdmin):
    list_display = (
        'permissions',
        'value',
    )


class DeployJobAdmin(admin.ModelAdmin):
    list_display = (
        'service',
        'status',
        'image_tag',
        'created_at',
        'completed_at',
    )


admin.site.register(Node, NodeAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(DeployJob, DeployJobAdmin)
admin.site.register(AccessKey, AccessKeyAdmin)
