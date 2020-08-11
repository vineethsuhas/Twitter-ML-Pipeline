from django import forms

from loader import models
from loader.utils import write_to_uploads


class OfflineLoaderForm(forms.ModelForm):
    OFFLINE_JOB_CHOICES = (
        ('', '-----'),
        ('job1', 'offline_classifier'),
    )

    offline_job = forms.ChoiceField(choices=OFFLINE_JOB_CHOICES)

    class Meta:
        model = models.OfflineLoader
        fields = '__all__'


class ProjectForm(forms.ModelForm):

    sample_offline_file = forms.FileField(required=False)

    class Meta:
        model = models.Project
        fields = '__all__'

    def save(self, commit=True):
        instance = super(ProjectForm, self).save(commit=False)

        if instance.offline_loader:
            upload_path = instance.offline_loader.file_path
            file = self['sample_offline_file'].value()
            if file:
                write_to_uploads(file, folder_name=upload_path, file_name=file.name)

        if commit:
            instance.save()
        return instance
