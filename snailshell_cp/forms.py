from django import forms

from snailshell_cp.models import DeployJob


class CreateDeployJobForm(forms.ModelForm):
    access_key = forms.CharField(max_length=255)

    class Meta:
        model = DeployJob
        fields = ['service', 'image_tag']
