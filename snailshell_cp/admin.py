from django.contrib import admin
from django.conf import settings
from django import forms
from django.core.exceptions import MultipleObjectsReturned

from fabric.api import execute
from snailshell_cp.clients.portainer import PortainerClient
from snailshell_cp.management.cluster_control.base import build_host_string
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
        super().clean()

        host_string = build_host_string(
            login=self.cleaned_data['login'],
            host=self.cleaned_data['host'],
            port=self.cleaned_data['port'],
        )

        try:
            execute(
                provision_slave_node,
                password=self.cleaned_data['password'],
                name=self.cleaned_data['name'],
                host=host_string,
            )
        except BaseClusterControlException as exc:
            raise forms.ValidationError(str(exc))

        raise forms.ValidationError('!!!')


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
