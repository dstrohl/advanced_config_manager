__author__ = 'dstrohl'


from AdvConfigMgr.config_exceptions import Error
from AdvConfigMgr.utils import VersionRange, slugify, interpolate
import copy
from fnmatch import fnmatchcase

class ConfigMigrationError(Error):

    def __init__(self, version_from, version_to, section, option, msg):
        msg = 'Error converting [{}.{}]: {}, converting from {} to {}'.format(section, option,
                                                                              msg, version_from, version_to)
        super(ConfigMigrationError, self).__init__(msg)


class ConfigMigrationManager(object):

    def __init__(self, section, *migration_dictionaries):
        self.section = section
        self.manager = section.manager

        self.migrations = []
        self._options_to_remove = []
        self._options_to_add = []

        self.live_version = self.section.version

        self.current_migration = None

        for md in migration_dictionaries:
            if not isinstance(md, (list, tuple)):
                md = [md]
            for m in md:
                self.migrations.append(self._make_migration_dict(m))

        self._int_key = self.manager._interpolation.key
        self._int_sep = self.manager._interpolation.sep
        self._int_enc = self.manager._interpolation.enc
        self._int_max_depth = self.manager._interpolation.max_depth

    '''
    def get_migration(self, version):
        """
        Will set the version manager to use based on the database version.  returns True if a version migration is
        found, False if no migration is found.
        """
        for vm in self.version_managers:
            if vm.use_this(version, self.live_version):
                return vm
        return None
    '''

    def migrate_section(self, version, section_dict):
        migrator = self.get_migration(version)

        tmp_dict = {}
        for option, value in section_dict.items():

            if option in migrator:
                tmp_dict[option] = migrator.convert(option, value)

        #: todo finish this

    '''
    def use_this(self, database_version, live_version):
        if database_version in self._from_version_range and live_version in self._to_version_range:
            return True
        return False

    def process_option(self, option):
        if self.keep_only and option not in self.action_dict:
            return False
        return True

    def convert(self, option, value):
        """
        This is the main interface with the version migration tool.  you pass the option name and the current value, and
        it will return the new option name (or old one if unchanged) and the migrated value.
        :param option:
        :param value:
        :return:
        """
        std_action = ['rename', 'pass', 'interpolate', 'converter']

        if option in self.action_dict:
            action_name = '_'+self.action_dict[option]['action']
            kwargs = copy.copy(self.action_dict[option])
            kwargs['old_value'] = value
            del kwargs['action']
            action = getattr(self, action_name)
            return action(**kwargs)
        else:
            if not self.keep_only:
                return option, value

        return None
    '''

    def _optionxform(self, option_name):
        return self.manager.optionxform(optionstr=option_name, extra_allowed='!*?[]')

    def _make_migration(self, migration_dict):

        tmp_md = {'from_version_range': VersionRange(version_class=self.manager._version_class,
                                                     sup_ver=migration_dict.get('stored_version', None),
                                                     min_ver=migration_dict.get('stored_version_min', None),
                                                     max_ver=migration_dict.get('stored_version_max', None)),
                  'to_version_range': VersionRange(version_class=self.manager._version_class,
                                                   sup_ver=migration_dict.get('live_version', None),
                                                   min_ver=migration_dict.get('live_version_min', None),
                                                   max_ver=migration_dict.get('live_version_max', None)),
                  'action_class': migration_dict.get('action_class', None),
                  'actions': {}}

        if 'actions' not in migration_dict:
            raise AttributeError('Section Migration must have actions defined')

        for a in migration_dict['actions']:
            tmp_action = {}
            tmp_a = copy.copy(a)
            if isinstance(a, dict):
                tmp_action['action_name'] = '_'+tmp_a.pop('action')
                tmp_action['option_name'] = tmp_a.pop('option_name')
                tmp_action['args'] = tmp_a
            elif isinstance(a, (tuple, list)):
                tmp_action['action_name'] = '_'+tmp_a.pop(0)
                tmp_action['option_name'] = self._optionxform(tmp_a.pop(0))
                tmp_action['args'] = tmp_a

            else:
                msg = 'Unknown migration action found: {}'.format(a)
                raise AttributeError(msg)

            if not hasattr(tmp_md['action_class'], tmp_action['action_name']):
                msg = 'Action Class Object does not have the {} action defined'.format(tmp_action['action_name'])
                raise AttributeError(msg)

            tmp_md['actions'][tmp_action['option_name']] = tmp_action
    '''
    @property
    def conv_from(self):
        return self.conversion_manager.conv_from

    @property
    def conv_to(self):
        return self.conversion_manager.conv_to

    def conv(self, option, old_value, **kwargs):
        self.option = option
        self.old_value = old_value
        return self.convert(option, old_value, **kwargs)

    def warn(self, msg):
        self.conversion_manager.warn(self.conv_from, self.conv_to, self.section, self.option, msg)

    def error(self, msg):
        raise ConfigMigrationError(self.conv_from, self.conv_to, self.section, self.option, msg)
    '''


class BaseMigrationActions(object):
    """
    To add new migration / conversion actions, subclass this and add new methods, each method MUST accept as the first
    two args "value" and "option_name", after that, you can use whatever, though make sure to be consistent with how
    you define things in the migration dictionary.

    You must also return a tuple of new_option_name, new_value, or None, None.

    If your migration requires removeing an option, call :py:meth:`BaseMigrationActions._remove` and it it requires
    adding a new option, call :py:meth:`BaseMigrationActions._new`.
    """

    def __init__(self, migration_manager):
        self._migration_manager = migration_manager

    # *************************************************************************************************************
    # **** Defined Actions
    # *************************************************************************************************************

    def _new(self, value, option_name):
        """
        This action should not be used by migration dictionaries and is instead an internal action used by other actions
        :return: None, None
        """
        self._migration_manager._options_to_add.append((option_name, value))
        return None, None

    def _remove(self, value, option_name):
        """
        Adds a the option to the "remove_options" queue and returns None, None
        :return: The existing option, value
        """
        self._migration_manager._options_to_remove.append(option_name)
        return None, None

    def _copy(self, value, option_name, new_option_name, interpolation_str=None):
        """
        Adds a copy of the option to the "new_options" queue.
        :return: The existing option, value
        """
        new_value = copy.copy(value)
        if interpolation_str is not None:
            new_option_name, new_value = self._interpolate(new_option_name, new_value, interpolation_str)

        self._new(new_value, new_option_name)
        return option_name, value

    def _rename(self, value, option_name, new_option_name, interpolation_str=None):
        """
        adds the option to the "remove options queue"
        :return: The new option name, value
        """
        self._remove(value, option_name)
        if interpolation_str is not None:
            return self._interpolate(new_option_name, value, interpolation_str)
        else:
            return new_option_name, value

    def _pass(self, value, option_name, interpolation_str=None):
        """
        Adds passes the option through the system without modification (unless the interpolation string is passed.)
        :return: The existing option, value
        """
        if interpolation_str is not None:
            return self._interpolate(option_name, value, interpolation_str)
        else:
            return option_name, value

    def _interpolate(self, value, option_name, interpolation_str):
        """
        Interpolates the string based on the interpolation rules, this can be called directly or through other actions.
        :return: The existing option, value
        """
        interpolation_str = interpolation_str.replace('%(__current_value__)', value)
        tmp_new_value = interpolate(interpolation_str,
                                    self.manager,
                                    max_depth=self._int_max_depth,
                                    key=self._int_key,
                                    key_sep=self._int_sep,
                                    key_enc=self._int_enc,
                                    current_path=self.section.name)
        return option_name, tmp_new_value




