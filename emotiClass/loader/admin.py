from django.contrib import admin
from django.core import urlresolvers

from loader import models
from loader.forms import ProjectForm, OfflineLoaderForm


class OfflineLoaderAdmin(admin.ModelAdmin):
    # form = OfflineLoaderForm
    list_display = ('name', 'storage', 'file_type', 'file_path')

    # fieldsets = (
    #     (None, {
    #         'fields': ('name', 'storage', 'file_type', 'file_path', 'offline_job'),
    #     }),
    # )


class TwitterTrackerAdmin(admin.ModelAdmin):
    list_display = ('name', 'search_terms')


class ProjectAdmin(admin.ModelAdmin):

    form = ProjectForm

    list_display = ('name', 'offline_loader_ref', 'twitter_tracker_ref')

    fieldsets = (
        (None, {
            'fields': ('name', 'offline_loader', 'twitter_tracker', 'sample_offline_file'),
        }),
    )

    def offline_loader_ref(self, obj):
        link = urlresolvers.reverse("admin:loader_offlineloader_change", args=[obj.offline_loader.id])
        return u'<a href="%s">%s</a>' % (link, obj.offline_loader.name)

    def twitter_tracker_ref(self, obj):
        link = urlresolvers.reverse("admin:loader_twittertracks_change", args=[obj.twitter_tracker.id])
        return u'<a href="%s">%s</a>' % (link, obj.twitter_tracker.name)

    offline_loader_ref.allow_tags = True
    twitter_tracker_ref.allow_tags = True


admin.site.register(models.OfflineLoader, OfflineLoaderAdmin)
admin.site.register(models.TwitterTracks, TwitterTrackerAdmin)
admin.site.register(models.Project, ProjectAdmin)
