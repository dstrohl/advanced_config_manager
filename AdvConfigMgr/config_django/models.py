__author__ = 'dstrohl'

from django.db import models
from django.conf import settings

DCM = getattr(settings, 'DJANGO_CONFIGURATION_MANAGER')
DCMS = DCM['django_config_manager']


class ConfigSections(models.Model):
    name = models.CharField(max_length=128, unique=True)
    description = models.CharField(max_length=256, blank=True, null=True)
    verbose_name = models.CharField(max_length=128, blank=True, null=True)
    hidden = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def options_count(self):
        return self.options.count()

    class Meta:
        verbose_name = DCMS['admin_section_title']
        verbose_name_plural = DCMS['admin_plural_section_title']


class ConfigOptions(models.Model):
    section = models.ForeignKey(ConfigSections, related_name='options')
    name = models.CharField(max_length=128, unique=True)
    value = models.TextField()
    default_value = models.TextField(blank=True, null=True)
    description = models.CharField(max_length=256, blank=True, null=True)
    verbose_name = models.CharField(max_length=128, blank=True, null=True)
    datatype = models.CharField(max_length=32)
    hidden = models.BooleanField(default=False)

    def __str__(self):
        tmp_ret = '{} = {}'.format(self.name, self.value)
        return tmp_ret

    class Meta:
        verbose_name = DCMS['admin_option_title']
        verbose_name_plural = DCMS['admin_plural_option_title']
