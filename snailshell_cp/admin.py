from django.contrib import admin
from django.conf import settings
from django import forms
from django.core.exceptions import MultipleObjectsReturned

from fabric.api import execute
from snailshell_cp.clients.portainer import PortainerClient
from snailshell_cp.management.cluster_control.base import build_host_string
from snailshell_cp.management.cluster_control.utils import add_ssh_host
from snailshell_cp.models import Node
from django.utils.safestring import mark_safe
from snailshell_cp.management.cluster_control import provision_slave_node
from snailshell_cp.management.cluster_control.base import BaseClusterControlException


def delete_node(modeladmin, request, queryset):
    try:
        node = queryset.get()
    except (MultipleObjectsReturned, Node.DoesNotExist):
        raise forms.ValidationError('Exactly one object has to be selected')

    if node.id == settings.PORTAINER_LOCAL_ENDPOINT_ID:
        raise forms.ValidationError('Can\'t remove the master node')


delete_node.short_description = 'Detach node from the cluster'


class NodeCreateForm(forms.ModelForm):
    password = forms.CharField(
        max_length=255,
        help_text='Password is only used to add an ssh key and is never stored anywhere.',
    )

    class Meta:
        model = Node
        exclude = ['id']

    def clean(self):
        cleaned_data = super().clean()

        host_string = build_host_string(
            login=cleaned_data['login'],
            host=cleaned_data['host'],
            port=cleaned_data['port'],
        )

        try:
            add_ssh_host(
                login=cleaned_data['login'],
                password=cleaned_data['password'],
                host=cleaned_data['host'],
                port=cleaned_data['port'],
            )
            # Configure docker on the remote machine
            # and add an entrypoint to Portainer
            response = execute(
                provision_slave_node,
                name=cleaned_data['name'],
                host=host_string,
                hostname=cleaned_data['host'],
            )

        except BaseClusterControlException as exc:
            raise forms.ValidationError(str(exc))

        self._obj_id = response[host_string]['entrypoint_id']
        return cleaned_data

    def save(self, *args, **kwargs):
        self.instance.id = self._obj_id
        return super().save(*args, **kwargs)


class NodeAdmin(admin.ModelAdmin):
    def identifier(self, obj):
        client = PortainerClient(settings.PORTAINER_EXTERNAL_URL)
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


admin.site.register(Node, NodeAdmin)
