import os
import subprocess
import datetime

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from jsonfield import JSONField


class Job(models.Model):
    tag = models.CharField(max_length=200)
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'loader'

    def __str__(self):
        return self.name


class OfflineLoader(models.Model):
    OFFLINE_STORAGE_CHOICES = (
        ('files', 'File System'),
        ('AWS', 'Amazon S3'),
        ('GCP', 'Google Storage')
    )
    OFFLINE_FILE_TYPES = (
        ('CSV', 'CSV'),
        ('JSON', 'JSON'),
        ('XML', 'XML')
    )
    OFFLINE_JOB_CHOICES = (
        ('job1', 'offline_classifier'),
    )
    name = models.CharField(max_length=200)
    storage = models.CharField(max_length=20, choices=OFFLINE_STORAGE_CHOICES)
    file_type = models.CharField(max_length=20, choices=OFFLINE_FILE_TYPES)
    file_path = models.CharField(max_length=200)
    job = models.ManyToManyField(Job)
    field_mappings = JSONField(help_text='Enter JSON Dictionary [Example: {"a":"b", "c":"d"}]')
    created_date = models.DateTimeField(default=datetime.datetime.now, editable=False)
    updated_date = models.DateTimeField(default=datetime.datetime.now, editable=False)

    class Meta:
        app_label = 'loader'

    def __str__(self):
        return self.name


class TwitterTracks(models.Model):
    ONLINE_JOB_CHOICES = (
        ('job1', 'online_loader'),
    )
    name = models.CharField(max_length=200)
    search_terms = models.TextField(max_length=500)
    job = models.ManyToManyField(Job)
    created_date = models.DateTimeField(default=datetime.datetime.now, editable=False)
    updated_date = models.DateTimeField(default=datetime.datetime.now, editable=False)

    class Meta:
        verbose_name = "Twitter Track"
        app_label = 'loader'

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=200)
    offline_loader = models.ForeignKey(OfflineLoader, related_name='project_offlineloader', null=True)
    twitter_tracker = models.ForeignKey(TwitterTracks, related_name='project_twittertracks', null=True)
    created_date = models.DateTimeField(default=datetime.datetime.now, editable=False)
    updated_date = models.DateTimeField(default=datetime.datetime.now, editable=False)

    class Meta:
        verbose_name = "Project"
        app_label = 'loader'

    def __str__(self):
        return self.name


@receiver(post_save, sender=Project, dispatch_uid="run_process")
def run_process(sender, instance, **kwargs):
    project_name = instance.name

    DEVNULL = open(settings.EC_LOG_FILE, 'wb')

    py_path = os.path.abspath(os.path.join(settings.ROOT_DIR, "../ec_venv/bin/python"))

    os.environ["PYSPARK_PYTHON"] = py_path
    os.environ["PYSPARK_DRIVER_PYTHON"] = py_path

    # Invoke the offline classifier.
    subprocess.Popen([py_path,
                      os.path.abspath(os.path.join(settings.BASE_DIR, "services/offline_classifier.py")),
                      "-p",
                      project_name], shell=False, stdout=DEVNULL, stderr=DEVNULL)

    # Invoke the streaming service
    subprocess.Popen([py_path,
                      os.path.abspath(os.path.join(settings.BASE_DIR, "services/streaming_service.py")),
                      "-p",
                      project_name], shell=False, stdout=DEVNULL, stderr=DEVNULL)

    # Invoke the online loader
    subprocess.Popen([py_path,
                      os.path.abspath(os.path.join(settings.BASE_DIR, "services/online_loader.py")),
                      "-p",
                      project_name], shell=False, stdout=DEVNULL, stderr=DEVNULL)

    # Invoke the online classifier
    subprocess.Popen([py_path,
                      os.path.abspath(os.path.join(settings.BASE_DIR, "services/online_classifier.py")),
                      "-p",
                      project_name], shell=False, stdout=DEVNULL, stderr=DEVNULL)
