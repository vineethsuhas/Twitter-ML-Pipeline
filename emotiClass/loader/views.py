import logging

from django.conf import settings
from django.shortcuts import render, HttpResponseRedirect
from django.contrib import messages

from loader.models import OfflineLoader, Project
from loader.utils import add_offline_loader, write_to_uploads, add_twitter_tracks


logger = logging.getLogger(settings.EC_LOG)
"""
Passing dict for model creation: https://stackoverflow.com/questions/1571570/can-a-dictionary-be-passed-to-django-models-on-create

request.body error: https://stackoverflow.com/questions/19581110/exception-you-cannot-access-body-after-reading-from-requests-data-stream

CSRF Ref: https://docs.djangoproject.com/en/dev/ref/csrf/

HTML ref: https://www.sanwebe.com/2014/08/css-html-forms-designs

File Uploads: 
    
    * https://stackoverflow.com/questions/15846120/uploading-a-file-in-django-with-modelforms
    
    * BigBasket: kirana/adminviews.py: 387 (request.FILES)
    
show_urls: https://stackoverflow.com/questions/1275486/django-how-can-i-see-a-list-of-urlpatterns

Models ChoiceField: https://stackoverflow.com/questions/8077840/choicefield-in-django-model

Complete Django Tutorials: https://tutorial.djangogirls.org/en/django_models/

Model Forms: https://docs.djangoproject.com/en/1.11/topics/forms/modelforms/
"""


def offline_loader_view(request):
    template = 'loader/offline_loader.html'
    ctx_dict = {}

    if request.method == 'POST':
        fields = {
            "name": request.POST.get('name'),
            "storage": request.POST.get('storage'),
            "file_type": request.POST.get('fileType'),
            "file_path": request.POST.get('filePath')
        }
        status = add_offline_loader(fields)
        if status:
            logger.debug("Successfully created Offline Loader")
        else:
            logger.debug("Failed to create Offline Loader")

        files = request.FILES
        if files:
            schema = files.get('schema')
            mapping = files.get('mapping')
            if schema:
                write_to_uploads(schema, file_name='schema')
            if mapping:
                write_to_uploads(mapping, file_name='mapping')

        return render(request, 'loader/success.html', ctx_dict)
    else:
        ctx_dict.update({
            "storage_opts": dict(OfflineLoader.OFFLINE_STORAGE_CHOICES).values(),
            "file_type_options": dict(OfflineLoader.OFFLINE_FILE_TYPES).values()
        })

    return render(request, template, ctx_dict)


def twitter_tracks_view(request):
    template = 'loader/twitter_tracks.html'

    if request.method == 'POST':
        fields = {
            "name": request.POST.get('name'),
            "search_terms": request.POST.get('tracks')
        }
        status = add_twitter_tracks(fields)
        if status:
            logger.debug("Successfully created Offline Loader")
        else:
            logger.debug("Failed to create Offline Loader")

        return render(request, 'loader/success.html')

    return render(request, template)


def project_upload_view(request):
    template = 'loader/project_upload.html'
    ctx_dict = {}

    if request.method == 'POST':
        # TODO: Send ID in the post, instead of name string
        prj_name = request.POST.get('project')
        if not prj_name:
            return

        # Get the given project object
        prj = Project.objects.get(name=prj_name)

        # Upload the file to the Offline Upload Path
        files = request.FILES
        if files:
            offline_upload_path = prj.offline_loader.file_path
            data = files.get('data')
            if data:
                write_to_uploads(data, folder_name=offline_upload_path, file_name=data.name)

        # Update the twitter tracks with the given tracks:
        tracks = request.POST.get('tracks')
        if tracks:
            tracker = prj.twitter_tracker
            cur_tracks = tracker.search_terms
            cur_tracks += tracks
            tracker.search_terms = cur_tracks
            tracker.save()

        messages.add_message(request, messages.INFO, 'Upload Successful')
        return HttpResponseRedirect('/admin')

    else:
        ctx_dict.update({
            "project_opts": list(Project.objects.values_list('name', flat=True))
        })

    return render(request, template, ctx_dict)
