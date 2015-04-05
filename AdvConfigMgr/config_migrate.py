__author__ = 'dstrohl'

from AdvConfigMgr.config_exceptions import Error
from AdvConfigMgr.utils import VersionRange, slugify, interpolate, _UNSET, UnSet
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
        self._options_to_add = {}

        self.live_version = self.section.version
        self.stored_version = _UNSET
        self.current_migration = None

        for md in migration_dictionaries:
            if not isinstance(md, (list, tuple)):
                md = [md]
            for m in md:
                self.migrations.append(self._parse_migration(m))

        self._int_key = self.manager._interpolation.key
        self._int_sep = self.manager._interpolation.sep
        self._int_enc = self.manager._interpolation.enc
        self._int_max_depth = self.manager._interpolation.max_depth

    def set_migration(self, version):
        """
        Will set the version manager to use based on the database version.  returns True if a version migration is
        found, False if no migration is found.
        """
        self.stored_version = version
        self.current_migration = None
        for m in self.migrations:
            if self.stored_version is None:
                if m['blank_stored_version'] and self.live_version in m['live_version_range']:
                    self.current_migration = m
                    return True
            else:
                if version in m['stored_version_range'] and self.live_version in m['live_version_range']:
                    self.current_migration = m
                    return True
        return False

    @property
    def options_to_remove(self):
        tmp_ret = copy.copy(self._options_to_remove)
        self._options_to_remove = None
        return tmp_ret

    def migrate_section(self, version, section_dict):
        if not self.set_migration(version):
            return section_dict

        option_list = self.current_migration['actions']
        actions = self.current_migration['action_class']
        keep_only = self.current_migration['keep_only']

        if actions is None:
            actions = BaseMigrationActions
        actions = actions(self)

        tmp_dict = {}
        for option, value in section_dict.items():
            new_option = None
            new_value = None
            match = False
            for option_name, option_args in option_list.items():
                if fnmatchcase(option_name, option):
                    match = True
                    action = getattr(actions, option_args['action_name'])
                    if isinstance(option_args['args'], dict):
                        new_option, new_value = action(value=value, option_name=option_name, **option_args['args'])
                    elif isinstance(option_args['args'], (list, tuple)):
                        new_option, new_value = action(value=value, option_name=option_name, *option_args['args'])
                    break

            if not keep_only and not match:
                new_option = option
                new_value = value

            if new_option is not None:
                tmp_dict[new_option] = new_value

        tmp_dict.update(self._options_to_add)

        return tmp_dict

    def _optionxform(self, option_name):
        return self.manager.optionxform(optionstr=option_name, extra_allowed='!*?[]')

    def _parse_migration(self, migration_dict):
        tmp_stored_version = migration_dict.get('stored_version', _UNSET)

        if tmp_stored_version is None:
            blank_stored_version = True
        elif tmp_stored_version is UnSet:
            blank_stored_version = False
            tmp_stored_version = None
        else:
            blank_stored_version = False

        tmp_md = {'stored_version_range': VersionRange(version_class=self.manager._version_class,
                                                       sup_ver=tmp_stored_version,
                                                       min_ver=migration_dict.get('stored_version_min', None),
                                                       max_ver=migration_dict.get('stored_version_max', None)),
                  'live_version_range': VersionRange(version_class=self.manager._version_class,
                                                     sup_ver=migration_dict.get('live_version', None),
                                                     min_ver=migration_dict.get('live_version_min', None),
                                                     max_ver=migration_dict.get('live_version_max', None)),
                  'action_class': migration_dict.get('action_class', None),
                  'blank_stored_version': blank_stored_version,
                  'actions': {},
                  'keep_only': migration_dict.get('keep_only', False)}

        if 'actions' not in migration_dict:
            raise AttributeError('Section Migration must have actions defined')

        for a in migration_dict['actions']:
            tmp_action = {}
            tmp_a = copy.copy(a)
            if isinstance(a, dict):
                tmp_action['action_name'] = '_' + tmp_a.pop('action')
                tmp_action['option_name'] = tmp_a.pop('option_name')
                tmp_action['args'] = tmp_a
            elif isinstance(a, (tuple, list)):
                tmp_action['action_name'] = '_' + tmp_a.pop(0)
                tmp_action['option_name'] = self._optionxform(tmp_a.pop(0))
                tmp_action['args'] = tmp_a

            else:
                msg = 'Unknown migration action found: {}'.format(a)
                raise AttributeError(msg)

            if not hasattr(tmp_md['action_class'], tmp_action['action_name']):
                msg = 'Action Class Object does not have the {} action defined'.format(tmp_action['action_name'])
                raise AttributeError(msg)

            tmp_md['actions'][tmp_action['option_name']] = tmp_action

        return tmp_md


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
        self._migration_manager._options_to_add[option_name] = value
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
        manager = self._migration_manager.manager
        interpolation_str = interpolation_str.replace('%(__current_value__)', value)
        tmp_new_value = interpolate(interpolation_str,
                                    manager,
                                    max_depth=self._migration_manager.manager._int_max_depth,
                                    key=self._migration_manager.manager._int_key,
                                    key_sep=self._migration_manager.manager._int_sep,
                                    key_enc=self._migration_manager.manager._int_enc,
                                    current_path=self._migration_manager.manager.section.name)
        return option_name, tmp_new_value




