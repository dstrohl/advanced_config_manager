__author__ = 'dstrohl'
__all__ = ['_DCM_SETTINGS_OPTIONS', '_DCM_SETTINGS_SECTION', '_DJANGO_DEFAULT_OPTIONS', '_DJANGO_SETTINGS_SECTION']

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
        'name': 'mongo_database_name',
        'default_value': '',
        'datatype': 'str',
        'verbose_name': 'Mongo Collection Name',
        'description': 'The collection or database name on the MongoDB server',
    },
    {
        'name': 'mongo_database_host',
        'default_value': '',
        'datatype': 'str',
        'verbose_name': 'Mongo host name',
        'description': 'The host name or IP address for the MongoDB server',
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
