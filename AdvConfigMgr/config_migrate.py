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

    def __init__(self, section, *version_managers):
        self.section = section
        self.manager = section.manager

        self.version_managers = []

        self.live_version = self.section.version

        self.current_migration = None

        for vm in version_managers:
            if not isinstance(vm, (list, tuple)):
                vm = [vm]
            for v in vm:
                self.version_managers.append(v(conversion_manager=self, section_obj=self.section))

    def get_migration(self, version):
        """
        Will set the version manager to use based on the database version.  returns True if a version migration is
        found, False if no migration is found.
        """
        for vm in self.version_managers:
            if vm.use_this(version, self.live_version):
                return vm
        return None

    def migrate_section(self, version, section_dict):
        migrator = self.get_migration(version)

        tmp_dict = {}
        for option, value in section_dict.items():

            if option in migrator:
                tmp_dict[option] = migrator.convert(option, value)

        #: todo finish this



class BaseVersionMigrator(object):
    """
    This class could have the following items:

    Note: storage managers call the migration managers, so only options on the storage methods being called will be
    migrated.  if options exist somewhere else, they will not be migrated until they are loaded.

    Note: storage managers with centralized storage, care shoudl be taken when migrating data to make sure that
    multiple versions are not in use concurrently.

    actions is a list of actions to take, each action definition is a tuple, with the first item being the action,
    and the remainder being parameters for the action if needed.

    Actions tuple examples

    Remove:
        These options will be removed and deleted from storage.
        ::

        ('remove','option_name')

    Rename::

        ('rename','old_option_name','new_option_name', <optional>'interpolation_string')

    Copy:
        This also allows copying from another section if a name is passed using dot notation.

        ::
        ('copy','old_option_name','new_option_name', <optional>'interpolation_string)
        ('copy','old_section.old_option_name,'new_option_name', <optional>'interpolation_string)

    Pass:
        These will just be passed through, not needed unless the "keep_only" flag is used

        ::
        ('pass','option_name')

    Interpolate:
        This runs the option through a simple interpolator, allowing for some simple conversions.

        ::

        ('interpolate','option_name','interpolation_string')

    Convert_Object:
        For more complex conversion needs, converters can be passed, kwargs dict can also be
        defined if needed.

        ::

        ('converter','option_name', converter_name, kwargs)

    example::

        [('remove','this_option'),
         ('copy','another_option','to_another_name')]

    The 'remove', 'pass', and 'converter' actions can all take glob type wildcards ('*', '?', '!', '[]')

    For interpolations, use '%(__current_value__)' for the current value, %(option_name), %(section_name.option_name) to
    pull in othe values.

    By default, options without actions will simply be passed through unless the "keep_only" flag is set.

    (1) Only record based storage managers will delete these from the storage medium.  others will rely on the object
    not being present in the config since the entire config is re-written to the storage overwriting the old one.

    """
    from_version_min = None
    from_version_max = None
    from_version = None

    to_version_min = None
    to_version_max = None
    to_version = None

    actions = None

    # if True, only options in the list will be kept, for record based storage all others will be deleted
    keep_only = False

    def __init__(self, conversion_manager, section_obj):
        self.conversion_manager = conversion_manager
        self.section = section_obj
        self.manager = section_obj.manager

        self._update_local_attr('from_version_min', None)
        self._update_local_attr('from_version_max', None)
        self._update_local_attr('from_version', None)

        self._update_local_attr('to_version_min', None)
        self._update_local_attr('to_version_max', None)
        self._update_local_attr('to_version', None)

        self._from_version_range = VersionRange(version_class=self.manager._version_class,
                                                sup_ver=self.from_version,
                                                min_ver=self.from_version_min,
                                                max_ver=self.from_version_max)

        self._to_version_range = VersionRange(version_class=self.manager._version_class,
                                              sup_ver=self.to_version,
                                              min_ver=self.to_version_min,
                                              max_ver=self.to_version_max)

        self.action_dict = {}
        self.add_actions = {}
        self.rem_actions = []

        self._int_key = self.manager._interpolation.key
        self._int_sep = self.manager._interpolation.sep
        self._int_enc = self.manager._interpolation.enc
        self._int_max_depth = self.manager._interpolation.max_depth

    def _optionxform(self, option_name):
        return self.manager.optionxform(optionstr=option_name, extra_allowed='!*?[]')

    def _make_update_actions(self):

        if self.actions is None:
            raise AttributeError('Section Migration must have actions defined')

        for a in self.actions:
            action_name = a[0]
            option_name = self._optionxform(a[1])
            
            if action_name == 'remove':
                self.rem_actions.append(option_name)
                # ('remove','option_name')

            elif action_name == 'rename':
                tmp_dict = dict(option_name=option_name, action=action_name, new_name=self._optionxform(a[2]))
                # ('rename','old_option_name','new_option_name', <optional>'interpolation_string')
                # ('copy','old_option_name','new_option_name', <optional>'interpolation_string)
                # ('copy','old_section.old_option_name,'new_option_name', <optional>'interpolation_string)
                if len(a) == 4:
                    tmp_dict['interpolate_str'] = a[3]
                else:
                    tmp_dict['interpolate_str'] = None
                self.action_dict[option_name] = tmp_dict
                self.rem_actions.append(option_name)

            elif action_name == 'pass' or action_name == 'interpolate_str':
                # ('pass','option_name')
                # ('interpolate_str','option_name','interpolation_string')
                tmp_dict = dict(option_name=option_name, action=action_name)
                if len(a) == 2:
                    tmp_dict['interpolate_str'] = a[2]
                else:
                    tmp_dict['interpolate_str'] = None
                self.action_dict[option_name] = tmp_dict

            elif action_name == 'copy':
                tmp_dict = dict(option_name=option_name, action=action_name, new_name=self._optionxform(a[2]))
                # ('rename','old_option_name','new_option_name', <optional>'interpolation_string')
                # ('copy','old_option_name','new_option_name', <optional>'interpolation_string)
                # ('copy','old_section.old_option_name,'new_option_name', <optional>'interpolation_string)
                if len(a) == 4:
                    tmp_dict['interpolate_str'] = a[3]
                else:
                    tmp_dict['interpolate_str'] = None
                self.add_actions[option_name] = tmp_dict

                self.action_dict[option_name] = dict(action='pass')

            elif action_name == 'converter':
                # ('converter','option_name', converter_name, kwargs)
                tmp_dict = dict(option_name=option_name, action=action_name, converter=a[2])
                if len(a) == 4:
                    tmp_dict['kwargs'] = a[3]
                else:
                    tmp_dict['kwargs'] = None
                self.action_dict[option_name] = tmp_dict

    def _update_local_attr(self, attr, val):
        if attr not in self.__dict__:
            setattr(self, attr, val)

    def use_this(self, database_version, live_version):
        if database_version in self._from_version_range and live_version in self._to_version_range:
            return True
        return False

    def process_option(self, option):
        if self.keep_only and option not in self.action_dict:
            return False
        return True

    def convert(self, option, value):
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

    def _rename(self, option_name, old_value, new_name, **junk):
        return new_name, old_value

    def _pass(self, option_name, old_value, interpolate_str=None, **junk):
        if interpolate_str is not None:
            return self._interpolate(option_name, old_value, interpolate_str)
        else:
            return option_name, old_value

    def _interpolate(self, option_name, old_value, interpolate_str, **junk):
        interpolate_str = interpolate_str.replace('%(__current_value__)', old_value)
        tmp_new_value = interpolate(interpolate_str,
                                    self.manager,
                                    max_depth=self._int_max_depth,
                                    key=self._int_key,
                                    key_sep=self._int_sep,
                                    key_enc=self._int_enc,
                                    current_path=self.section.name)
        return option_name, tmp_new_value

    def _converter(self, option_name, old_value, converter, kwargs=None, **junk):
        return converter(option_name, old_value, **kwargs)

    '''
    def _copy(self, old_name, old_value, new_name, interpolate_str=None, **junk):
    '''


    def __contains__(self, item):
        return self.process_option(item)



class BaseConverterClass(object):

    section = None
    manager = None

    section_conversion_manager = None
    conversion_manager = None

    def __init__(self):
        self.option = None
        self.old_value = None

    def convert(self, option_name, old_value, **kwargs):
        return option_name, old_value

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


class DemoMultBy100Class(BaseConverterClass):

    def convert(self, option_name, old_value, **kwargs):
        if not isinstance(old_value, int):
            self.error('old value is not an int')
        return option_name, old_value * 100



