__author__ = 'dstrohl'
__all__ = 'dcm_factory'

"""
This module is a shim for the django-advanced-config app that allows use of the advanced config manager in django
frameworks.
"""

from .advconfigmgr import ConfigManager
from copy import deepcopy


_DCM_SETTINGS_OPTIONS = [
    {
        'name': 'show_in_admin',
        'default_value': True,
        'description': 'Show the sections and options sections in the django admin (if used)',
    },
    {
        'name': 'sections_in_admin',
        'datatype': 'list',
        'default_value': None,
        'description': 'list of the sections in the admin, if None, this will show all non-hidden sections',
    },
    {
        'name': 'admin_section_title',
        'default_value': 'Configuration Section',
        'description': 'the title for the configuration section in the admin',
    },
    {
        'name': 'admin_option_title',
        'default_value': 'Configuration Option',
        'description': 'the title for the configuration options in the admin',
    },
    {
        'name': 'admin_plural_section_title',
        'default_value': 'Manage Configuration Sections',
        'description': 'the plural title for the configuration section in the admin',
    },
    {
        'name': 'admin_plural_option_title',
        'default_value': 'Manage Configuration Options',
        'description': 'the plural title for the configuration options in the admin',
    },
    {
        'name': 'admin_allow_add_section',
        'default_value': False,
        'description': 'can the admin add a section',
    },
    {
        'name': 'admin_allow_add_option',
        'default_value': False,
        'description': 'can the admin add an option',
    },
    {
        'name': 'admin_allow_del_section',
        'default_value': False,
        'description': 'can the admin delete a section',
    },
    {
        'name': 'admin_allow_del_option',
        'default_value': False,
        'description': 'can the admin delete an option',
    },
    {
        'name': 'use_ini_for_settings',
        'default_value': True,
        'description': 'will use a local ini file for managing django settings',
    },
    {
        'name': 'ini_file_name',
        'default_value': 'settings.ini',
        'description': 'what should the ini file be named.',
    },
]

_DCM_SETTINGS_SECTION = {
    'name': 'django_config_manager',
    'verbose_name': 'Configuration Manager Options',
    'description': 'Settings used to manage the configuration manager.',
    'storage': 'local',
    'store_default': True,
    'options': _DCM_SETTINGS_OPTIONS,
}

_DJANGO_DEFAULT_OPTIONS = [
    {
        'name': 'debug',
        'default_value': True,
        'datatype': 'bool',
        'verbose_name': 'Debug mode',
        'description': 'set to False for debug mode',
    },
    {
        'name': 'allowed_hosts',
        'default_value': [],
        'datatype': 'list',
        'verbose_name': 'List of allowed hosts to test web server',
        'description': 'A list of IP addresses or networks that are allowed to access the test server',
    },
    {
        'name': 'sql_lite_database_name',
        'default_value': 'db.sqlite3',
        'datatype': 'str',
        'verbose_name': 'SQLite database file name',
        'description': 'The name of the SQLite database file to use',
    },
    {
        'name': 'language_code',
        'default_value': 'en-us',
        'datatype': 'str',
        'verbose_name': 'Language Code',
        'description': 'The language code for the system',
    },
    {
        'name': 'timezone',
        'default_value': 'UTC',
        'datatype': 'str',
        'verbose_name': 'Default Timezone',
        'description': 'the default timezone for the system',
    },

]

_DJANGO_SETTINGS_SECTION = {
    'name': 'settings',
    'verbose_name': 'Django Settings',
    'description': 'These are the basic settings used for Django.',
    'storage': 'local',
    'store_default': True,
    'options': _DJANGO_DEFAULT_OPTIONS,
}


class DjangoConfigManager(ConfigManager):
    _DEFAULT_CLI_MANAGER = None
    _default_cli_name = None
    _autosave_names = ['*', ]
    _autoload_names = ['local', ]


class DcmFactory(object):

    def __init__(self):
        self._DCM = None

    def get_dcm(self, ini_file_name=None, base_options=None, version=None):
        """
        instantiates the DjangoConfigManager with some base Django Options

        all options passed will be added to the "settings" section.
        :param ini_file_name: String file name and path of the ini file to read from.
        :param base_options: list of full option dictionaries or single dictionary of options.
            if a single dict is passed, it is assuemd to be a simple option dict, so if you
            need to pass a single full option dictionary, you need to enclose it in a list.
        :param version: version string
        :return: returns a DjangoConfigManager instance loaded with initial options.
        """

        if self._DCM is None:

            storage_config = dict(file={
                'storage_name': 'local',
                'filename': ini_file_name,
            })

            if base_options is not None:
                tmp_opts = []
                if isinstance(base_options, dict):
                    for name, value in base_options.items():
                        tmp_o = dict(name=name, default_value=value)
                        tmp_opts.append(tmp_o)

                django_options = merge_lists_of_dicts(base_options, _DJANGO_DEFAULT_OPTIONS, 'name')

                _DJANGO_SETTINGS_SECTION['options'] = django_options

            self._DCM = DjangoConfigManager(version=version,
                                            storage_config=storage_config,
                                            section_list=[_DCM_SETTINGS_SECTION, _DJANGO_SETTINGS_SECTION])

            # self._DCM.read()

        return self._DCM

dcm_factory = DcmFactory()


def merge_lists_of_dicts(source, target, key, source_default=None, target_default=None):
    """
    assumes two lists of dictionaries
    merge source into target, replacing anythng in target that exists, keeping the order of target, recortds in the
    source that are not in the target will be added at the end.

    if a default dictionary is passed, any empty fields in the source or target will be filled in with the default
    fields.

    :param list source:
    :param list target:
    :param str key:
    :param dict source_default:
    :param dict target_default:
    :return:
    """
    tmp_ret = []

    tmp_source = {}
    for s in source:
        if source_default is not None:
            tmp_item = deepcopy(source_default)
            tmp_item.update(s)
        else:
            tmp_item = s

        tmp_source[s[key]] = tmp_item

    for t in target:
        if target_default is not None:
            tmp_item = deepcopy(target_default)
            tmp_item.update(t)
        else:
            tmp_item = t

        tmp_item.update(tmp_source.pop(t[key], {}))

        tmp_ret.append(tmp_item)

    for key, item in tmp_source.items():
        tmp_ret.append(item)

    return tmp_ret