import os
import logging

from django.conf import settings

from loader.models import OfflineLoader, TwitterTracks


logger = logging.getLogger(settings.EC_LOG)


def get_or_create_dir(dir_name):
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
        return True
    return False


# def copy_file_to_tmp(file, folder_name=None):
#     TMP_DIR = os.path.join(settings.UPLOAD_DIR, 'tmp')
#     get_or_create_dir(TMP_DIR)
#     if folder_name:
#         TMP_DIR = os.path.join(TMP_DIR, folder_name)
#         get_or_create_dir(TMP_DIR)
#     file_path = os.path.join(TMP_DIR, file.name)
#     file_destination = open(file_path, 'wb+')
#     for chunk in file.chunks():
#         file_destination.write(chunk)
#     file_destination.close()
#     return file_path


def write_to_uploads(file, folder_name=settings.UPLOAD_DIR, file_name=""):
    get_or_create_dir(folder_name)
    file_path = os.path.join(folder_name, file_name)
    file_destination = open(file_path, 'wb+')
    for chunk in file.chunks():
        file_destination.write(chunk)
    file_destination.close()
    return file_path


class FileHandler:

    def __init__(self, dir=None, file_name=None):
        self.dir = dir if dir else os.path.join(settings.UPLOAD_DIR, 'tmp')
        self.validate_dir()
        self.file = file_name if file_name else self.get_file(file_name)

    def validate_dir(self):
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)

    def get_file(self, name=None):
        file_path = os.path.join(self.dir, name)
        return file_path

    def write(self, data):
        file_destination = open(self.file, 'wb+')
        for chunk in data.chunks():
            file_destination.write(chunk)
        file_destination.close()
        return True


def add_offline_loader(fields):
    name = fields.pop('name')

    if not name:
        return False

    try:
        ofl = OfflineLoader.objects.get_or_create(name=name)[0]
        for attr, value in fields.items():
            setattr(ofl, attr, value)
        ofl.save()
    except Exception as e:
        logger.debug("Exception occurred while creating offline loader --- ".format(str(e)))
        return False

    return True


def add_twitter_tracks(fields):
    name = fields.pop('name')

    if not name:
        return False

    try:
        tt = TwitterTracks.objects.get_or_create(name=name)[0]
        for attr, value in fields.items():
            setattr(tt, attr, value)
        tt.save()
    except Exception as e:
        logger.debug("Exception occurred while creating twitter tracks --- ".format(str(e)))
        return False

    return True
