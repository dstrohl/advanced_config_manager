__author__ = 'dstrohl'

from django.contrib import admin
from .models import ConfigOptions, ConfigSections
from django.conf import settings

DCM = getattr(settings, 'DJANGO_CONFIGURATION_MANAGER')
DCMS = DCM['django_config_manager']


class OptionsAdmin(admin.ModelAdmin):
    model = ConfigOptions
    fields = (('section', 'name', 'verbose_name'), ('value', 'default_value'), 'description',  'datatype')
    readonly_fields = ('section', 'name', 'verbose_name', 'default_value', 'description',  'datatype')
    list_display = ('section', 'verbose_name', 'value', 'default_value')
    list_display_links = ('verbose_name', )

    def save_model(self, request, obj, form, change):
        obj.save()

    def has_add_permission(self, request):
        #: TODO, This
        return True


    def has_delete_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        qs = super(OptionsAdmin, self).get_queryset(request)
        # qs.filter(hidden=False, section__name__in=DCMS['sections_in_admin'])
        return qs


class OptionsInline(admin.TabularInline):
    model = ConfigOptions
    extra = 0
    fields = ('verbose_name', 'value', 'default_value', 'datatype')
    readonly_fields = ('verbose_name', 'default_value', 'datatype')


class SectionAdmin(admin.ModelAdmin):
    model = ConfigSections
    fields = (('name', 'verbose_name', 'options_count'), 'description')
    list_display = ('verbose_name', 'options_count')
    list_display_links = ('verbose_name', )
    readonly_fields = ('name', 'verbose_name', 'options_count', 'description')
    inlines = [OptionsInline, ]

if DCMS['show_in_admin']:
    admin.site.register(ConfigOptions, OptionsAdmin)
    admin.site.register(ConfigSections, SectionAdmin)
