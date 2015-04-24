__author__ = 'dstrohl'
from django.apps import AppConfig
from django.conf import settings
from ..config_storage import BaseConfigRecordBasedStorageManager
from ..utils.base_utils import make_list


class ConfigDjangoStorage(BaseConfigRecordBasedStorageManager):
    storage_type_name = 'Django Storage Manager'
    storage_name = 'django'
    force_strings = True  #: True if the storage only accepts strings
    config_sections_model = None
    config_options_model = None
    standard = True

    def custom_config(self, config_dict):

        self.app_config = config_dict['app_config']
        self.config_sections_model = config_dict.get('config_sections_model', 'ConfigSections')
        self.config_options_model = config_dict.get('config_options_model', 'ConfigOptions')

        if isinstance(self.config_sections_model, str):
            self.config_sections_model = self.app_config.get_model(self.config_sections_model)

        if isinstance(self.config_options_model, str):
            self.config_options_model = self.app_config.get_model(self.config_options_model)

    def read_from_storage(self, flat=False, default_section_name=None, data=None, **kwargs):
        tmp_sections = self.config_sections_model.objects.all()
        data = {}

        for s in tmp_sections:
            tmp_sec = {}
            for o in s.options.all():
                tmp_sec[o.name] = o.value
            data[s.name] = tmp_sec

        return data

    def write_to_storage(self, data_dict, flat=False, **kwargs):
        """
        will write the config from the system to a database
        """

        for section, options in data_dict.items():
            tmp_sec, created = self.config_sections_model.objects.update_or_create(
                name=section,
                defaults={'description': self.manager[section].description,
                          'verbose_name': self.manager[section].verbose_name,
                          'hidden': self.manager[section].hidden})

            for option, value in options.items():
                opt_rec = self.manager[section].item(option)
                self.config_options_model.objects.update_or_create(
                    name=option,
                    section=tmp_sec,
                    defaults={
                        'description': opt_rec.description,
                        'value': value,
                        'default_value': opt_rec.default_value,
                        'verbose_name': opt_rec.verbose_name,
                        'datatype': opt_rec.datatype,
                        'hidden': opt_rec.hidden, })

        return data_dict

    def delete_record(self, section, option):
        tmp_sec = self.config_sections_model.objects.get(name=section)
        self.config_options_model.objects.filter(section=tmp_sec, name=option).delete()
        if tmp_sec.options.count() == 0:
            tmp_sec.delete()


class DjangoConfigManagerApp(AppConfig):
    name = 'cif.config_manager.config_django'
    verbose_name = 'Application Configuration'

    def ready(self):
        dcm = getattr(settings, 'DJANGO_CONFIGURATION_MANAGER', None)
        if dcm is None:
            raise AttributeError('DJANGO_CONFIGURATION_MANAGER must be set to an instance of DjangoConfigManager')

        storage_config = {'database': {'app_config': self}}

        dcm.storage.register_storage(ConfigDjangoStorage,
                                     storage_name='database',
                                     make_default=True,
                                     storage_config=storage_config)

        # dcm.read(storage_names='database')
        # dcm.write(sections=['settings', 'django_config_manager'], override_tags=True, storage_names='database')
