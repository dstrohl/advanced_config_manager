__author__ = 'dstrohl'

"""Configuration file parser.

A configuration file consists of sections, lead by a "[section]" header,
and followed by "name: value" entries, with continuations and such in
the style of RFC 822.

Intrinsic defaults can be specified by passing them into the
ConfigParser constructor as a dictionary.

class:

ConfigParser -- responsible for parsing a list of
                    configuration files, and managing the parsed database.

    methods:

    __init__(defaults=None, dict_type=_default_dict, allow_no_value=False,
             delimiters=('=', ':'), comment_prefixes=('#', ';'),
             inline_comment_prefixes=None, strict=True,
             empty_lines_in_values=True):
        Create the parser. When `defaults' is given, it is initialized into the
        dictionary or intrinsic defaults. The keys must be strings, the values
        must be appropriate for %()s string interpolation.

        When `dict_type' is given, it will be used to create the dictionary
        objects for the list of sections, for the options within a section, and
        for the default values.

        When `delimiters' is given, it will be used as the set of substrings
        that divide keys from values.

        When `comment_prefixes' is given, it will be used as the set of
        substrings that prefix comments in empty lines. Comments can be
        indented.

        When `inline_comment_prefixes' is given, it will be used as the set of
        substrings that prefix comments in non-empty lines.

        When `strict` is True, the parser won't allow for any section or option
        duplicates while reading from a single source (file, string or
        dictionary). Default is True.

        When `empty_lines_in_values' is False (default: True), each empty line
        marks the end of an option. Otherwise, internal empty lines of
        a multiline option are kept as part of the value.

        When `allow_no_value' is True (default: False), options without
        values are accepted; the value presented for these is None.

    sections()
        Return all the configuration section names, sans DEFAULT.

    has_section(section)
        Return whether the given section exists.

    has_option(section, option)
        Return whether the given option exists in the given section.

    options(section)
        Return list of configuration options for the named section.

    read(filenames, encoding=None)
        Read and parse the list of named configuration files, given by
        name.  A single filename is also allowed.  Non-existing files
        are ignored.  Return list of successfully read files.

    read_file(f, filename=None)
        Read and parse one configuration file, given as a file object.
        The filename defaults to f.name; it is only used in error
        messages (if f has no `name' attribute, the string `<???>' is used).

    read_string(string)
        Read configuration from a given string.

    read_dict(dictionary)
        Read configuration from a dictionary. Keys are section names,
        values are dictionaries with keys and values that should be present
        in the section. If the used dictionary type preserves order, sections
        and their keys will be added in order. Values are automatically
        converted to strings.

    get(section, option, raw=False, vars=None, fallback=_UNSET)
        Return a string value for the named option.  All % interpolations are
        expanded in the return values, based on the defaults passed into the
        constructor and the DEFAULT section.  Additional substitutions may be
        provided using the `vars' argument, which must be a dictionary whose
        contents override any pre-existing defaults. If `option' is a key in
        `vars', the value from `vars' is used.

    getint(section, options, raw=False, vars=None, fallback=_UNSET)
        Like get(), but convert value to an integer.

    getfloat(section, options, raw=False, vars=None, fallback=_UNSET)
        Like get(), but convert value to a float.

    getboolean(section, options, raw=False, vars=None, fallback=_UNSET)
        Like get(), but convert value to a boolean (currently case
        insensitively defined as 0, false, no, off for False, and 1, true,
        yes, on for True).  Returns False or True.

    items(section=_UNSET, raw=False, vars=None)
        If section is given, return a list of tuples with (name, value) for
        each option in the section. Otherwise, return a list of tuples with
        (section_name, section_proxy) for each section, including DEFAULTSECT.

    remove_section(section)
        Remove the given file section and all its options.

    remove_option(section, option)
        Remove the given option from the given section.

    set(section, option, value)
        Set the given option.

    write(fp, space_around_delimiters=True)
        Write the configuration state in .ini format. If
        `space_around_delimiters' is True (the default), delimiters
        between keys and values are surrounded by spaces.
"""

import copy
from collections import OrderedDict
from distutils.version import LooseVersion, Version

from AdvConfigMgr.config_exceptions import *
from AdvConfigMgr.config_interpolation import Interpolation
from AdvConfigMgr.config_migrate import ConfigMigrationManager
from AdvConfigMgr.config_ro_dict import ConfigDict
from AdvConfigMgr.config_transform import Xform
from AdvConfigMgr.config_types import *
from AdvConfigMgr.storage_managers.config_storage import *
from AdvConfigMgr.utils import args_handler, make_list
from AdvConfigMgr.utils.unset import _UNSET

__all__ = ['ConfigManager', 'ConfigSection', 'ConfigOption']


class ConfigOption(object):
    def __init__(self, section, name, *args, **kwargs):
        """
        An individual option in the config

        :param ConfigSection section:  A pointer to the ConfigSection object that this is a part of
        :param str name: The name of the config object.  This is transformed by the optionxform method in the main
            config manager.  by default this is converted to lowercase
        :param object default_value: Default= _UNSET the default value for the item. If set to :py:class:`_UNSET` this
            is considered to not have a default.  (this allows None to be a valid default setting.
        :param str data_type: Default=None: This is the type of data that is stored in the option.  this accepts : None,
            'str', 'int', 'float', 'list', 'dict' additional data types can be defined using the DataTypeBase class.
            If set to None and there is a default value set, this will take the datatype of the default value,
            otherwise it will be set to 'str'
        :param verbose_name: Default=None This is the long name for the option (that can show up in the options
            configuration screen or help screen)  This is set to a title case version of the option name with spaces
            replacing '_'
        :type verbose_name: str or None
        :param description: Default=None This is the long description for the option, available in the help screens.
        :type description: str or None
        :param cli_option: Default=None  This allows the option to be changed via the CLI on startup, this would be a
            string, tuple or dictionary of options that configure how the cli commands will be handled.
        :type cli_option: str or None
        :param object validations: Default=None: This is a set of validation classes to be run for any options saved.
        :param bool keep_if_empty: Default=True: If set to False the option will be deleted when the value is cleared
            AND there is no set default value.
        :param bool do_not_change: Default=False If set to True, this will not allow the user to change the option after
            initial loading.
        :param bool do_not_delete: Default=False  If set to True, this will not allow the user to delete the option.
        :param bool required_after_load: Default = False, If set to true, the app should not start without this being
            set. if there is a CLI_option available, the app should prompt the user for that option, if not, the app
            should fail with a usefull message.
        :param bool autoconvert: will attempt to autoconvert values to the datatype, this can be disabled if needed.
            (some types of data may not autoconvert correctly.)
        """
        self._section = section
        self._manager = self._section._manager

        junk, self._name = self._xf(name)

        self._value = _UNSET

        #self._data = data_value
        #self._value = self._data._value
        #self.default_value = self._data._default_value

        # only exists for IDE happiness.        
        self.default_value = _UNSET
        self.datatype = None
        self.verbose_name = None
        self.description = None
        self.cli_options = None
        self.validations = None
        self.keep_if_empty = True
        self.do_not_change = False
        self.do_not_delete = False
        self.required_after_load = False
        self.autoconvert = True
        # IDE happiness section ends

        args_list = (('default_value', _UNSET),
                     ('datatype', None),
                     ('verbose_name', None),
                     ('cli_options', None),
                     ('validations', None),
                     ('description', None),
                     ('keep_if_empty', True),
                     ('do_not_delete', False),
                     ('do_not_change', False),
                     ('required_after_load', False),
                     ('autoconvert', True))

        args_handler(self, args, args_list, kwargs)

        # self._value = _UNSET
        section, self._name = self._xf(self._name)

        ip.debug('INIT option: ', self._name).a()

        if self.datatype is None:
            if self.default_value is not _UNSET:
                self.datatype = self.default_value.__class__.__name__
            else:
                self.datatype = 'str'

        self._datatype_manager = self._manager._data_type_manager(self.datatype)(self.validations)
        self._validator = data_type_generator(self.datatype)(self.validations)

        if self.verbose_name is None:
            self.verbose_name = self._name.title()
        if self.do_not_change and self.is_empty:
            raise NoOptionError(option=self.name, section=self._section.name)

        if self.cli_options is not None:
            ip.debug('option has CLI settings: ', self.cli_options)
            cli_args = {'dest': self.name}
            if self.description is not None:
                cli_args['help'] = self.description

            if isinstance(self.cli_options, (list, tuple, str)):
                cli_args['flags'] = self.cli_options

            elif isinstance(self.cli_options, dict):
                cli_args.update(self.cli_options)

            cli_data_flag = cli_args.pop('data_flag', True)

            if self._datatype_manager._type_class == bool:

                if cli_data_flag:
                    cli_args['action'] = 'store_true'
                else:
                    cli_args['action'] = 'store_false'

            tmp_flags = []
            for f in make_list(cli_args['flags']):
                if f[0] != '-':
                    tmp_flags.append('-' + f)
                else:
                    tmp_flags.append(f)
            cli_args['flags'] = tmp_flags

            if 'default' in cli_args:
                if cli_args['default'] is None:
                    del cli_args['default']
            else:
                if self.has_default_value:
                    cli_args['default'] = self.default_value

            self.cli_options = cli_args
            self._section._register_cli(self)

        ip.debug('created option: ', self._repr_str).s()

    @property
    def name(self):
        return self._name

    def _xf(self, option):
        return self._section._xf(option)

    def _xf_this_sect(self, section):
        return self._section._xf_this_sec(section)


    def validated(self, value):
        return self._datatype_manager(value)

    @property
    def can_delete(self):
        tmp_ret = (self.default_value == _UNSET) and (not self.do_not_delete)
        ip.debug('check delete [', self.path, ']').a()
        ip.debug('default_value: ', self.default_value)
        ip.debug('do_not_delete: ', self.do_not_delete)
        ip.debug('can_delete: ', tmp_ret)

        return tmp_ret

    @property
    def _has_cli(self):
        if self.cli_options is None:
            return False
        else:
            return True

    def clear(self):
        ip.debug('clear option [', self.path, ']').a()

        if self.has_set_value:
            if self.has_default_value:

                self._value = self.default_value
                ip.debug('setting to default value: ', self.default_value).s()
            else:
                self._value = _UNSET
                ip.debug('setting to _UNSET').s()

        if not self.keep_if_empty and not self.has_default_value:
            self._section.delete(self.name, force=True)

    def delete(self):
        return self._section.delete(self.name)

    def _get(self, as_string=False):
        """
        internal use get, does not do interpolation.
        :param as_string:
        :return:
        """
        tmp_value = copy.deepcopy(self.value)

        if as_string:
            tmp_value = self._datatype_manager.to_string(tmp_value)

        ip.debug('get option [', self.path, '], returning ', tmp_value)

        return tmp_value

    def get(self, raw=False, as_string=False):
        """
        Gets the current value or default interpolated value.

        :param raw: if set to True will bypass the interpolater
        :return: the interpolated value or default value.
        """
        tmp_ret = self._get(as_string=as_string)
        if not raw:
            tmp_ret = self._manager._interpolator.before_get(self._section.name, tmp_ret)
        return tmp_ret

    def to_write(self, raw=False, as_string=False):
        """
        gets data from the system to save to a storage module,

        :param raw: if set to True will bypass the interpolater
        :return: the interpolated value or default value.
        :param as_string: returns the value as a strong (passing through the datatype module to_string method)
        :return: the interpolated value or default value.
        """
        tmp_ret = self._get(as_string=as_string)
        if not raw:
            tmp_ret = self._manager._interpolator.before_write(self._section.name, tmp_ret)
        return tmp_ret

    def _set(self, value, validate=True, force=False, from_string=False):
        """
        internal use set, assumes that if interpolator is None, no interpolation (this is different from .get in that
        .get will set the default interpolater unless raw = True

        :param validate:
        :param force: will skip lock checks
        :param from_string: will force conversion from string
        :return:
        """

        if self.autoconvert:
            value = self._datatype_manager.auto_convert(value)
        elif from_string:
            value = self._datatype_manager.from_string(value)

        if value != self._value:

            if not self.do_not_change or force:

                if self.has_default_value and value == self.default_value:
                    self.clear()
                    ip.debug('set option [', self.path, '], to default value [', value, ']')

                if validate:
                    self.validated(value)

                self._value = value
                ip.debug('set option [', self.path, '], to ', value)
            else:
                if self._manager._raise_error_on_locked_edit:
                    raise ForbiddenActionError('Change attempted on locked option [%s]' % self.name)
                ip.debug('option [', self.path, '], is locked')
        else:
            ip.debug('option [', self.path, '], already set to ', value)

        return value

    def set(self, value, raw=False, validate=True, force=False):
        """
        Sets the current value.

        :param value: the value to set
        :param raw: if set to True will bypass the interpolater
        :param validate: if False will bypass the validation steps
        :param force: if True will bypass the lock checks
        :return: the interpolated value or default value.
        """
        if not raw:
            tmp_ret = self._manager._interpolator.before_set(self._section.name, value)
        else:
            tmp_ret = value

        return self._set(tmp_ret, validate=validate, force=force)

    def from_read(self, value, raw=False, validate=True, from_string=False):
        """
        adds data from a storage module to the system, this ignores the 'do_not_add' flag.

        :param value: the value to add
        :param raw: if set to True will bypass the interpolater
        :param validate: if False will bypass the validation steps
        :param from_string: if True will convert from string
        :return: the interpolated value or default value.
        """
        if not raw:
            tmp_ret = self._manager._interpolator.before_write(self._section.name, value)
        else:
            tmp_ret = value

        return self._set(tmp_ret, validate=validate, force=True, from_string=from_string)

    # *******************************************************************************************************
    # ****  OPTION : Pass through methods
    # *******************************************************************************************************

    @property
    def is_empty(self):
        return self.default_value == _UNSET and self._value == _UNSET

    @property
    def path(self):
        return self._section.name + '.' + self.name

    @property
    def has_set_value(self):
        return self._value != _UNSET

    @property
    def has_default_value(self):
        return self.default_value != _UNSET

    @property
    def is_default(self):
        return self.has_default_value and not self.has_set_value

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        if self.has_set_value:
            return self._value
        if self.has_default_value:
            return self.default_value
        return _UNSET

    '''
    @property
    def path(self):
        return self._data.path

    @property
    def is_empty(self):
        return self._data.is_empty
    @property
    def has_set_value(self):
        return self._data.has_set_value

    @property
    def has_default_value(self):
        return self.default_value != _UNSET

    @property
    def is_default(self):
        return self._data.has_default_value

    @property
    def value(self):
        return self._data.value
    '''
    # *******************************************************************************************************
    # ****  OPTION : Magic Methods
    # *******************************************************************************************************

    def __len__(self):
        return len(self.value)

    def __call__(self, *args):
        if args:
            self.set(args[0])
        return self.get()

    def __contains__(self, item):
        return item in self.value

    def __str__(self):
        return str(self.value)

    @property
    def _repr_str(self):
        try:
            return 'ConfigOption: {} [Value: {} / Default: {}]'.format(self.path, self.value, self.default_value)
        except EmptyOptionError:
            return 'ConfigOption: {} [-No current value or default value set-]'.format(self.path)

    def __repr__(self):
        return self._repr_str


class ConfigSection(object):
    """
    A single section of a config
    """

    def __init__(self, manager, name,
                 verbose_name=None,
                 description=None,
                 storage_write_to=None,
                 storage_read_from_only=None,
                 # keep_if_empty=True,
                 store_default=False,
                 locked=False,
                 allow_create_on_load=True,
                 allow_create_on_set=True,
                 option_defaults=None,
                 cli_section_title=None,
                 cli_section_desc=None,
                 version=None,
                 version_option_name=None,
                 version_migrations=None,
                 options=None):
        """
        :param ConfigManager manager: A pointer to the config manager
        :param str name: The name of the section
        :param str verbose_name: The verbose name of the section
        :param str description: A long description of the section
        :param str storage_write_to: The tag of the storage location to save to, if None, the section will be saved to
            the default location, if '-' it will not be saved in save_all operations, if "*", section will be saved to
            all configured storage locations. Sections can be saved manually to any storage if needed.
        :param storage_read_from_only: options from storage with tags in this list will be read.  If None
            (default) then options in storage will be always be used.  This allows restricting options to specific
            storage locations.
            CLI options, if configured, will always overwrite data from storage.
        :type storage_read_from_only: str or list
        :param bool store_default: store defaults in storage medium
        :param bool locked: if True, do not allow any changes to the section
        :param bool allow_create_on_load: if True, options will be created if they are in the stored data, if false, they
            must be configured first.
        :param bool allow_create_on_set: if True, options can be created using a dictionary set proces, if False, they need
            to be configured first.
        :param str cli_section_title: the name of the section in the CLI (if sectioned), Defaults to verbose_name
        :param str cli_section_desc: the description for the section in the CLI (if sectioned), Defaults to description
        :param str version: the version number of the section, if None, this will take the version number of the
            ConfigManager object.
        :param str version_option_name: allows for overriding the ConfigManager's version_option_name setting.
        """

        self._manager = manager

        # self._data_dict = data_dict

        if name is None:
            raise AttributeError('Section must have a name')

        self._name, junk = self._manager._xf(name)

        if verbose_name is None:
            self.verbose_name = name.title()
        else:
            self.verbose_name = verbose_name
        self.description = description
        self.storage_write_to = storage_write_to
        self.storage_read_from_only = storage_read_from_only
        self.store_default = store_default
        self.allow_create_on_load = allow_create_on_load
        self.allow_create_on_set = allow_create_on_set
        self.locked = locked
        if option_defaults:
            self.option_defaults = option_defaults
        else:
            self.option_defaults = {}
        self._options = {}
        self.dict_type = {}
        self.last_failure_list = []
        self._cli_section_options = {}

        if cli_section_desc is None:
            self._cli_section_options['description'] = description
        else:
            self._cli_section_options['description'] = cli_section_desc

        if cli_section_title is None:
            self._cli_section_options['title'] = self.verbose_name
        else:
            self._cli_section_options['title'] = cli_section_title

        self._cli_args = {}

        self.version = version

        if version is None:
            if self._manager.version is None:
                if self._manager._enforce_versioning:
                    raise AttributeError('Versioning is required, but no version found')
            else:
                self.version = self._manager.version
        else:
            self.version = self._manager._version_class(version)

        if version_option_name is None:
            self.version_option_name = self._manager._version_option_name.format(section=self.name)
        else:
            self.version_option_name = version_option_name.format(section=self.name)

        if self.version is not None:
            tmp_version_dict = {'name': self.version_option_name,
                                'default_value': str(self.version),
                                'verbose_name': 'Section Version Number',
                                'description': 'The version number for this section',
                                'keep_if_empty': True,
                                'do_not_change': True,
                                'do_not_delete': True}

            self.add(tmp_version_dict)

        if version_migrations is not None and version_migrations:
            self._migrations = ConfigMigrationManager(self, version_migrations)
        else:
            self._migrations = None

        if options is not None:
            self.add(options, force_load=True)

    def _debug_(self):
        # ip.toggle_silent(False)
        ip.debug('DEBUG DUMP FOR CONFIG SECTION').a(2)

        ip.debug('name : ', self._name)
        ip.debug('verbose name : ', self.verbose_name)
        ip.debug('description : ', self.description)
        ip.debug('version : ', self.version)
        ip.debug('version option name : ', self.version_option_name)
        ip.debug('option defaults : ', self.option_defaults)
        ip.debug('options : ', self._options)

        ip.s().debug('SECURITY FLAGS').a()
        ip.debug('locked              : ', self.locked)
        ip.debug('allow create on set : ', self.allow_create_on_set)

        ip.s().debug('STORAGE FLAGS').a()
        ip.debug('store defaults : ', self.store_default)
        ip.debug('storage write to : ', self.storage_write_to)
        ip.debug('storage read from only : ', self.storage_read_from_only)
        ip.debug('allow create on load : ', self.allow_create_on_load)
        ip.debug('last fail list : ', self.last_failure_list)
        ip.debug('cli section options : ', self._cli_section_options)
        ip.debug('cli args : ', self._cli_args)

        ip.s().debug('MIGRATION FLAGS').a()
        ip.debug('migrations', self._migrations)

        ip.s(2)

    def migrate_dict(self, storage_version, section_dict):
        if self._migrations is None:
            return section_dict
        else:
            return self._migrations.migrate_section(storage_version, section_dict)

    @property
    def section_ok_after_load(self):
        """
        validates that all options that are required "after_load" have either a set or default value
        :return:
        :rtype boolean:
        """
        self.last_failure_list = []

        for o in self:
            if o.required_after_load and o.is_empty:
                self.last_failure_list.append(o.name)
                return False
        return True
    '''
    @property
    def _data(self):
        if self._manager._lockable_data_dict:
            ip.debug('Section data dictionary is lockable, unlocking')
            self._manager._data_dict._editable = True
        return self._data_dict

    def _data_lock(self):
        ip.debug('Section data dictionary is lockable, unlocking')
        self._manager._data_lock()
    '''

    def _xf(self, option, glob=False):
        return self._manager._xform.both(option, option_or_section='option', section=self._name, glob=glob)

    def _xf_this_sec(self, section):
        return section is _UNSET or section == self.name or section is None

    def get(self, option, fallback=_UNSET, raw=False):
        """
        gets the value of an option

        :param option: the name of the option
        :param fallback: a value to return if the option is empty
        :param raw: a flag to skip interpolation
        :return:
        """
        section, option = self._xf(option)

        if self._xf_this_sec(section):
            try:
                return self._options[option].get(raw=raw)
            except KeyError:
                if fallback == _UNSET:
                    raise NoOptionError(option, self.name)
                else:
                    return fallback
        else:
            return self._manager[section].get(option, fallback=fallback, raw=raw)

    def set(self, option, value, raw=False, validate=True, force=False):
        """
        Sets an option value.

        :param option: the name of the option to set
        :param value: the value to set
        :param raw: if set to True will bypass the interpolater
        :param validate: if False will bypass the validation steps
        :param force: if True will bypass the lock checks, used for loading data.
        :return: the interpolated value or default value.
        """

        section, option = self._xf(option)

        if self._xf_this_sec(section):
            if option not in self:
                if self.allow_create_on_set:
                    self.add(option, value)
                else:
                    raise NoOptionError(option, self.name)

            if not self.locked or force:
                self._options[option].set(value,
                                          raw=raw,
                                          validate=validate,
                                          force=force)
        else:
            self._manager[section].set(option, value, raw=raw, validate=validate, force=force)

    def from_read(self, option, value, raw=False, validate=True):
        """
        adds data from a storage module to the system, this ignores the 'do_not_add' flag.
        :param str option: option name
        :param value: the value to add
        :param bool raw: True if the interpolation needs to be bypassed.
        :param bool validate: True if validation should happen.
        :return:
        """

        section, option = self._xf(option)
        if self._xf_this_sec(section):
            try:
                self._options[option].from_read(value,
                                                raw=raw,
                                                validate=validate,
                                                force=True)
            except NoOptionError:
                if self.allow_create_on_load:
                    self.add(option)
                    self._options[option].from_read(value,
                                                    raw=raw,
                                                    validate=validate,
                                                    force=True)
                else:
                    raise NoOptionError(section=self.name, option=option)
        else:

            self._manager[section].from_read(value, raw=raw, validate=validate)

    def to_write(self, option, raw=False, as_string=False):
        """
        gets data from the system to save to a storage module
        :param bool raw:
        :param bool as_string:
        :return:
        """
        section, option = self._xf(option)

        if self._xf_this_sec(section):
            return self._options[option].to_write(raw=raw, as_string=as_string)
        else:
            return self._manager[section].to_write(option, raw=raw, as_string=as_string)

    def option(self, option):
        return self.item(option)

    def item(self, option):
        section, option = self._xf(option)

        if self._xf_this_sec(section):
            return self._options[option]
        else:
            return self._manager[section].item(option)

    def items(self, raw=False):
        """
        Return a list of (name, value) tuples for each option in a section.

        All interpolations are expanded in the return values, based on the
        defaults passed into the constructor, unless the optional argument
        'raw' is true.
        
        :param bool raw: True if data should not be interpolated.
        
        """
        tmp_items = list(self._options)
        tmp_ret = []
        for i in tmp_items:
            tmp_ret.append((i, self.get(i, raw=raw)))
        return tmp_ret

    def delete(self, options, force=False, forgiving=False):
        """
        Will delete a list of options.

        :param options: Option name or list of option names.
        :type: str or list
        :param bool force: True will delete the object even if it has a default_value without checking for value or lock.
        :param bool forgiving: True will return False if the option is not found, False, will raise NoOptionError.
        :return: True if all deletes passed, False if not.  if False, a list of the failed options is stored in
            :py:attr:`ConfigSection.last_failure_list`
        :rtype: bool
        """
        if self.locked and not force:
            ip.debug('section ', self._name, ' locked ')
            return False

        options = make_list(options)
        ip.debug('delete options: ', options)
        self.last_failure_list = []
        tmp_ret = True
        for o in options:

            section, option = self._xf(o)
            if self._xf_this_sec(section):
                ip.debug('trying option: ', option)

                try:
                    opt = self._options[option]
                    if opt.has_default_value and not force:
                        ip.debug('section ', self._name, ' delete-clearing option ', option)
                        opt.clear()
                    elif not opt.do_not_delete or force:
                        ip.debug('section ', self._name, ' deleteing option ', option)
                        del self._options[option]
                        #del self._data[option]
                        #self._data_lock()
                    else:
                        ip.debug('option ', option, ' delete prohibited')
                        self.last_failure_list.append(option)
                        tmp_ret = False
                except KeyError:
                    ip.debug('option ', option, ' not found ')
                    if forgiving:
                        self.last_failure_list.append(option)
                        tmp_ret = False
                    else:
                        raise NoOptionError(option=option, section=section)
            else:
                self._manager[section].delete(option, force=force, forgiving=forgiving)
        return tmp_ret

    def clear(self, options, forgiving=False):
        """
        Will set the option to the default value or to unset as long as long as the section is not locked.

        :param options: option name or list of option names
        :type options: str or list
        :param bool forgiving: True will return False if the option is not found, False, will raise NoOptionError.
        :return: True if all deletes passed, False if not.  if False, a list of the failed options is stored in
            self.last_failure_list
        :rtype: bool
        :raises NoOptionError: If the option does not exist. and forgiving is False.
        """
        if self.locked:
            ip.debug('section ', self._name, ' locked ')
            self.last_failure_list.extend(make_list(options))
            return False

        options = make_list(options)
        self.last_failure_list = []
        tmp_ret = True
        for o in options:
            section, option = self._xf(o)
            if self._xf_this_sec(section):

                ip.debug('trying option: ', option)
                try:
                    ip.debug('section ', self._name, ' clearing option ', option)
                    self._options[option].clear()
                except KeyError:
                    ip.debug('option ', option, ' not found ')
                    if forgiving:
                        self.last_failure_list.append(option)
                        tmp_ret = False
                    else:
                        raise NoOptionError(option=option, section=section)
            else:
                tmp_ret = self._manager[section].clear(option, forgiving=forgiving)

        return tmp_ret

    def _register_cli(self, option):
        ip.a().debug('Registering CLI Option on load: ', option.name)
        if self._manager._default_cli_name is not None:
            self._manager.storage.get(self._manager._default_cli_name).reset_cache()
            tmp_args = option.cli_options
            tmp_dest = option.cli_options['dest']
            tmp_flags = make_list(tmp_args['flags'])
            for f in tmp_flags:
                if f in self._manager._cli_flags:
                    raise DuplicateCLIOptionError(option.name, f)
                self._manager._cli_flags.append(f)

            self._cli_args[tmp_dest] = tmp_args
            self._manager._cli_args[tmp_dest] = option
        ip.s()

    def load(self, option, value, *args, **kwargs):
        """
        Loads value into system, can create new options if "allow_create_on_load" is set.

        :param name: Option Name
        :param value: Option Value
        :param args: as per ConfigOption class (passed through)
        :param kwargs: as per ConfigOption class (passed through)
        """

        if option not in self:
            if not self.allow_create_on_load:
                raise NoOptionError

            if 'datatype' not in kwargs:
                kwargs['datatype'] = value.__class__.__name__

            self._add(option, *args, force_load=True, **kwargs)

        self.set(option, value)

    @property
    def options_list(self):
        return list(self._options.keys())

    def add(self, *args, **kwargs):
        """
        Adds new option definition to the system

        args, kwargs: config options can also be passed in args/kwargs, in a number of formats.

        Examples:

        This does not set any default values::

            add('option1', 'option2', 'option3')
    
        Seperate dictionaries::

            add(full_option_dict, full_option_dict)
    
        A list of dictionaries::

            add([full_option_dict, full_option_dict])
    
        A list of sets with option_name and default value.::

            add([('option1',default_value),('option2',default_value)]
    
        If default value is a dict, this will not work, if a dict is passed, it is assumed to be a full_option_dict::

            add(option1=default_value1, option2=default_value2, option3=default_value3)
    
            add(option1={full_option_dict}, option2={full_option_dict))
    
        These can be mixed, so the following would be valid::

            add('option1', full_option_dict, [full_option_dict, full_option_dict], [('option2',default_value)])

        full_option_dict Example (with defaults):
            'name': '<name of option>',
            'default_value': _UNSET,
            'datatype': None,
            'verbose_name': None,
            'description': None,
            'cli_option': None,
            'validations': None,
            'do_not_change': False,
            'do_not_delete': False,
            'required_after_load': False,

        .. note::
            * If a default value is a dictionary, it must be passed within a full option dict.
            * See ConfigOption for option_dict parameters.
            * If a full option dict is passed as an arg (not kwarg) it must contain a 'name' key.
            * Args and kwargs can be mixed if needed... for example this is also a valid approach::

                add(option1, <full_option_dict>, option3=default_value, option4={full_option_dict}

            * If options are repeated in the same commane, kwargs will take precdence over args,
              and new options will overwrite old ones.
            * if there are existing options in the section with the same name, an error will be raised.
        """
        tmp_options = []
        force_load = kwargs.pop('force_load', False)
        if args:
            for arg in args:
                if isinstance(arg, (str, dict)):
                    tmp_options.append(arg)
                elif isinstance(arg, (list, tuple)):
                    for a in arg:
                        if isinstance(a, (list, tuple)):
                            tmp_arg = {'name': a[0], 'default_value': a[1]}
                            tmp_options.append(tmp_arg)
                        else:
                            tmp_options.append(a)

        if kwargs:
            for name, arg in iter(kwargs.items()):
                tmp_arg = {}
                if isinstance(arg, dict):
                    tmp_arg.update(arg)
                    tmp_arg['name'] = name
                else:
                    tmp_arg['name'] = name
                    tmp_arg['default_value'] = arg

                tmp_options.append(tmp_arg)

        for o in tmp_options:

            if isinstance(o, dict):
                try:
                    name = o.pop('name')
                    self._add(name, force_load=force_load, **o)
                except KeyError:
                    raise AttributeError('config parameter dict does not contain "name"')
            elif isinstance(o, str):
                self._add(o, force_load=force_load)

    def _add(self, name, *args, **kwargs):
        """
        Adds new option definition to the system
        :param str name: option name
        :param set args: as per ConfigOptionClass (passed through)
        :param dict kwargs: as per ConfigOptionClass (passed through)
        :return:
        """
        with_defaults = copy.copy(self.option_defaults)
        with_defaults.update(kwargs)

        force = kwargs.pop('force_load', False)

        if self.locked and not force:
            raise LockedSectionError(section=self._name)

        if self.locked:
            kwargs['do_not_change'] = True
            kwargs['do_not_delete'] = True

        section, option = self._xf(name)
        if self._xf_this_sec(section):
            # tmp_data_rec = self._data.add(option, _UNSET)
            self._options[option] = ConfigOption(self, option, *args, **with_defaults)
            # self._data_lock()
        else:
            if force:
                kwargs['force_load'] = True
            self._manager[section]._add(option, *args, **kwargs)

    @property
    def name(self):
        # The name of the section on a proxy is read-only.
        return self._name

    def __repr__(self):
        return 'ConfigSection {}, {} options defined'.format(self._name, len(self))

    def __getitem__(self, option):
        section, option = self._xf(option)
        if self._xf_this_sec(section):
            return self.get(option)
        else:
            return self._manager[section].get(option)

    def __setitem__(self, option, value):
        """ sets item value """
        section, option = self._xf(option)
        if self._xf_this_sec(section):
            self.set(option, value)
        else:
            self._manager[option] = value

    def __delitem__(self, option):
        return self.delete(option)

    def __contains__(self, option):
        section, option = self._xf(option)
        if self._xf_this_sec(section):
            return option in self._options
        else:
            return option in self._manager

    def __len__(self):
        return len(self._options)

    def __iter__(self):
        for key, opt in self._options.items():
            yield opt


class ConfigManager(object):
    """
    :param allow_no_value: allow empty values.
    :param empty_lines_in_values:
    :param allow_add_from_storage: allow adding sections and options directly from the storage
    :param allow_create_on_set: allows sections to be created when the set command is used.
        the set command can only be used to set the values of options, so this REQUIRES using dot-notation.
    :param no_sections: this will disable all sections and all options will be accessible from the base manager
        object.  (this creates a section named "default_section".)
        .. warning:: converting from simple configurations to sections may require manual data minipulation!
    :param section_defaults: a dictionary of settings used as defaults for all sections created
    :param interpolation: can be defined if interpolation is requested or required.
    :param str section_option_sep: defines a seperator character to use for getting options using the dot_notation
        style of query. defaults to '.', in which case options can be queried by calling
        ConfigManager[section.option] in addition to ConfigManager[section][option].  If this is set to None, dot
        notation will be disabled.
    :param cli_program: the name of the program for the cli help screen (by default this will use the program run
        to launch the app)
    :param cli_desc: the text to show above the arguments in the cli help screen.
    :param cli_epilog: the text to show at the end of the arguments in the cli help screen.
    :param raise_error_on_locked_edit: if True, will raise an error if an attempt to change locked options,
        if False (default) the error is suppressed and the option will not be changed.
    :param storage_managers: a list of storage managers to use, if none are passed, the configuration will not be
        able to be saved.
    :param cli_parser_name: the name of the cli parser if not the default.  set to None if the CLI parser
        is not to be used.
    :param cli_group_by_section: True if cli arguments shoudl be grouped by section for help screens.
    :param version_class: 'loose', 'strict', a subclass of the Version class or None for no versioning.
    :type version_class: Version or str or None
    :param str version: the version number string.
    :param str version_option_name: the option named used to store the version for each section, {section} will be
        replaced by the name of the section.
    :param bool version_allow_unversioned: if True, the system will import unversioned data, if false, the version
        of the data must be specified when importing any data.
    :param bool version_enforce_versioning: if True, the system will raise an error if no version is set at the
        section or base level.
    :param bool version_disable_cross_section_copy:  if True, cross section copy will not work.  Used when you have
        plugins from different authors and you want to segment them.
    :param list version_make_migrations: this is a list of migrations that can be performed, (see :doc:`migration`\ )
    :param kwargs: if "no_sections" is set, all section options can be passed to the ConfigManager object.
    """
    _name = 'System Configuration'

    # Helper Classes Used
    _DEFAULT_INTERPOLATION = Interpolation
    _DEFAULT_STORAGE_PLUGINS = (ConfigFileStorage, )
    _DEFAULT_STORAGE_MANAGER = StorageManagerManager
    _DEFAULT_CLI_MANAGER = ConfigCLIStorage
    _DEFAULT_XFORM = Xform
    _DEFAULT_SECTION_CLASS = ConfigSection
    _DEFAULT_OPTION_CLASS = ConfigOption
    _DEFAULT_MIGRATION_CLASS = ConfigMigrationManager
    _DEFAULT_VERSION_MANAGER_CLASS = LooseVersion
    # _DEFAULT_DATA_DICT = ConfigDict
    _DEFAULT_DATA_TYPE_MANAGER = DataTypeGenerator
    _DEFAULT_DATA_TYPES = (DataTypeInt, DataTypeDict, DataTypeBoolean,
                           DataTypeFloat, DataTypeList, DataTypeStr, DataTypeLooseVersion,
                           DataTypeStrictVersion)
    _DEFAULT_DICT_TYPE = OrderedDict

    # Storgae Options
    _default_cli_name = 'cli'

    # Security Values
    _allow_add_from_storage = True
    _allow_create_on_set = True
    _raise_error_on_locked_edit = False

    # Section Configuration
    _no_sections = False
    _no_section_section_name = "__DEFAULT__"
    _section_option_sep = '.'

    # CLI Settings
    _cli_program = None
    _cli_desc = None
    _cli_epilog = None
    _cli_group_by_section = True

    # Migration and Versions
    _version_option_name = '{section}_version_number'
    _allow_unversioned = True
    _enforce_versioning = False
    _disable_cross_section_copy = False

    # allow_no_value = False
    # empty_lines_in_values = True

    def __init__(self, version=None,
                 migrations=None,
                 storage_config=None,
                 storage_managers=None,
                 default_storage_managers=None,):
        """

        :param ConfigDict data_dict: any dictionary that can support the number of levels needed.
        :param str version: the string version number.
        :param list migrations: a list of migration dictionaries.
        :param dict storage_config: a dictionary of storage configuration dictionaries.  These would be in the format
            of {'storage_name':{<config_dict>},'storage_name':{<config_dict>}}.  See specific storage managers for
            details of the config dict entries.
        :param BaseStorageManager storage_managers: a list or set of storage managers to use, if not passed, the file
            storage manager is used.
        :param list default_storage_managers: a list or string indicating the default storage manager(s) names to use
            if no names are passed during read/write operations.  if None (the default) all conifgured storage managers
            are polled.
        """

        if self._no_sections:
            self._section_option_sep = None
            self._cli_group_by_section = False
            self._disable_cross_section_copy = True

        self._xform = self._DEFAULT_XFORM(self._section_option_sep)
        self._interpolator = self._DEFAULT_INTERPOLATION(self, self._xform, sep=self._section_option_sep)

        self._data_type_manager = self._DEFAULT_DATA_TYPE_MANAGER(*self._DEFAULT_DATA_TYPES)

        '''
        if data_dict is None:
            self._data_dict = self._DEFAULT_DATA_DICT(self)
        else:
            self._data_dict = data_dict

        if issubclass(type(self._data_dict), self._DEFAULT_DATA_DICT):
            self._lockable_data_dict = True
            self._data_dict._interpolator = self._interpolator
            self._data_dict._xform = self._xform
        else:
            self._lockable_data_dict = False
        '''

        self.last_fail_list = []
        self._sections = self._DEFAULT_DICT_TYPE()

        self._cli_parser_args = {'prog': self._cli_program, 'description': self._cli_desc, 'epilog': self._cli_epilog}

        self._version_class = self._DEFAULT_VERSION_MANAGER_CLASS

        if version is not None:
            ip.debug('Version is not None, setting version to: ', version)
            self._version = self._version_class(version)
        else:
            self._version = None

        self._cli_flags = []
        self._cli_args = {}

        self._storage = self._DEFAULT_STORAGE_MANAGER(self,
                                                      cli_manager=self._DEFAULT_CLI_MANAGER,
                                                      cli_parser_name=self._default_cli_name,
                                                      storage_config=storage_config,
                                                      default_storage_managers=default_storage_managers)

        if storage_managers is None:
            tmp_storage_managers = self._DEFAULT_STORAGE_PLUGINS
        else:
            if not isinstance(storage_managers, (list, tuple)):
                tmp_storage_managers = (storage_managers, )
            else:
                tmp_storage_managers = storage_managers
        for s in tmp_storage_managers:
            self._storage.register_storage(s)




        if migrations is None:
            self._migrations = []
        else:
            self._migrations = migrations

        if self._no_sections:
            self.add_section(self._no_section_section_name, force_add_default=True)

    def _debug_(self):
        ip.si(False)
        ip.debug('DEBUG DUMP FOR CONFIG MANAGER').a(2)

        ip.debug('Name     : ', self.name)

        ip.debug('SECURITY FLAGS').a()
        ip.debug('Allow Add from Storage      : ', self._allow_add_from_storage)
        ip.debug('Allow create on set         : ', self._allow_create_on_set)
        ip.debug('Disable Cross Section Copy  : ', self._disable_cross_section_copy)
        ip.debug('Section Options Sep         : ', self._section_option_sep)

        ip.s().debug('SECTION').a()
        ip.debug('No Sections            : ', self._no_sections)
        ip.debug('Sections               : ', self.sections)

        ip.s().debug('INTERPOLATION').a()
        ip.debug('Interpolation Class : ', self._interpolator)

        ip.s().debug('VERSIONS').a()
        ip.debug('Version                  : ', self._version)
        ip.debug('Allow Unversioned        : ', self._allow_unversioned)
        ip.debug('Enforce Versioning       : ', self._enforce_versioning)
        # ip.debug('Root Version Option Name : ', self._version_option_name)
        ip.debug('Version Class            : ', self._version_class)

        ip.s().debug('STORAGE').a()
        ip.debug('Storage Managers : ', self._storage)

        ip.debug('Group CLI By Section        : ', self._cli_group_by_section)
        ip.debug('CLI Flags                   : ', self._cli_flags)
        ip.debug('CLI Args                    : ', self._cli_args)
        ip.debug('CLI Parser Args             : ', self._cli_parser_args)

        ip.debug('Raise Error on Locked Files : ', self._raise_error_on_locked_edit)

        ip.debug('Last fail list              : ', self.last_fail_list)

        ip.s().debug('MIGRATION').a()
        ip.debug('Migration Managers : ', self._migrations)
        ip.s(2)

    def _xf(self, section, option=_UNSET):
        return self._xform.both(section, option_or_section='section', option=option)

    @property
    def version(self):
        return self._version

    @property
    def name(self):
        return self._name

    @property
    def sections(self):
        tmp_ret = []
        for s in self._sections:
            tmp_ret.append(s)
        """Return a list of section names"""
        return tmp_ret

    def get_sec_migrations(self, section):
        tmp_ret = []
        for m in self._migrations:
            tmp_section, tmp_option = self._xf(m['section_name'])
            if tmp_section == section:
                tmp_ret.append(m)
        return tmp_ret

    @property
    def config_ok_after_load(self):
        for s in self:
            if not s.section_ok_after_load:
                tmp_name = s.name + '.' + '/'.join(s.last_failure_list)
                self.last_fail_list.append(tmp_name)
                return False
        return True

    '''
    @property
    def _data(self):
        if self._lockable_data_dict:
            self._data_dict._editable = True
            ip.debug('Base data dictionary is lockable, unlocking')
        return self._data_dict

    def _data_lock(self):
        if self._lockable_data_dict:
            self._data_dict._editable = False
            ip.debug('Base data dictionary is lockable, locking')
    '''

    def add_section(self, section, force_add_default=False, **kwargs):
        """Create a new section in the configuration.

        Raise DuplicateSectionError if a section by the specified name
        already exists.
        """
        if self._no_sections and not force_add_default:
            raise SimpleConfigError(section)

        section, option = self._xf(section)

        kwargs['version_migrations'] = self.get_sec_migrations(section)

        if section in self._sections:
            raise DuplicateSectionError(section)
        # tmp_data_rec = self._data.add(section)
        self._sections[section] = ConfigSection(self, section, **kwargs)
        # self._data_lock()

    def add(self, *args, **kwargs):
        """
        Adds configuration options::

            add('section1', 'section2', 'section3')
            add(section_def_dict1, section_def_dict2, section_def_dict3)
            add([list of section_def_dicts])
            add('section_name.option_name', 'section_name.option_name')

            add(section_name1='option_name1', section_name2='option_name2')
            add(section_name=section_def_dict, section_name2=section_def_dict)
            add(section_name=[list_of_option_names or dicts], section_name=(list of option names or dicts]

        section_def_dict keys

        ======================= ==========  ============================================================================
        Key                     Default     Description
        ======================= ==========  ============================================================================
        'name'                  None        The name of the section
        'verbose_name'          None        The verbose name of the section
        'description'           None        A long description of the section
        'storage'               None        The name of the storage location (if used)
        'keep_if_empty'         False       Keep the section even if all options ahve been deleted
        'store_default'         False       Store defaults in storage medium
        'locked'                False       If True, do not allow any changes to the section
        'allow_create_on_load'  True        Allow new options to be created directly from the storage medium
                                            for example, if you hand edit the ini file and add new options
        'option_defaults'       None        Allows a dict to be passed with defaults for any new options in this section
                                            this will replace any system wide option defaults specified.
        'options'               None        Provides a list of options to be added to the section,
        ======================= ==========  ============================================================================

        .. note:: When no sections are used, this will redirect to :py:meth:`ConfigSection.add`

        """

        if self._no_sections:
            return self._sections[self._no_section_section_name].add(*args, **kwargs)

        tmp_sections = []
        if args:
            for arg in args:
                if isinstance(arg, str):
                    if '.' in arg:
                        tmp_sec = {}
                        tmp_arg = arg.split(',', 1)
                        tmp_sec['name'] = tmp_arg[0]
                        tmp_sec['options'] = tmp_arg[1]
                        tmp_sections.append(tmp_sec)
                    else:
                        tmp_sections.append(arg)

                if isinstance(arg, dict):
                    tmp_sections.append(arg)
                elif isinstance(arg, (list, tuple)):
                    tmp_sections.extend(arg)

        if kwargs:
            for name, sec in iter(kwargs.items()):
                tmp_sec = {}
                if isinstance(sec, dict):
                    tmp_sec.update(sec)
                    tmp_sec['name'] = name
                else:
                    tmp_sec['name'] = name
                    tmp_sec['options'] = sec

                tmp_sections.append(tmp_sec)

        for s in tmp_sections:

            if isinstance(s, dict):
                try:
                    name = s.pop('name')
                    self.add_section(name, **s)
                except KeyError:
                    raise AttributeError('config parameter dict does not contain "name"')
            elif isinstance(s, str):

                self.add_section(s)

    # ****************************************************************************************************************
    # **                Storage Methods
    # ****************************************************************************************************************

    @property
    def storage(self):
        return self._storage

    def write(self, sections=None, storage_names=None, override_tags=False, **kwargs):
        """
        runs the write to storage process for the selected or configured managers

        :param storage_names: If None, will write to all starnard storage managers, if a string or list, will write to the
            selected ones following the configured tag settings.
        :param sections: If None, will write to all sections, if string or list, will write to the selected ones
            following the configured tag settings.
        :param override_tags: if True, this will override the configured storage tag settings allowing things like
            exporting the full config etc.
        :return: if ONLY one storage_tag is passed, this will return the data from that manager if present.
        """
        return self.storage.write(sections=sections, storage_names=storage_names, override_tags=override_tags, **kwargs)

    def read(self, sections=None, storage_names=None, override_tags=False, data=None, **kwargs):
        """
        runs the read from storage process for the selected or configured managers

        :param storage_names: If None, will read from all starnard storage managers, if a string or list, will read from
            the selected ones following the configured tag settings.
        :param sections: If None, will read from all sections, if string or list, will read from the selected ones
            following the configured tag settings.
        :param override_tags: if True, this will override the configured storage tag settings allowing things like
            exporting the full config etc.
        :param data: if a single storage tag is passed, then data can be passed to that storage manager for saving.
            this will raise an AssignmentError if data is not None and more than one storage tag is passed.
        """
        self.storage.read(sections=sections, storage_names=storage_names, override_tags=override_tags, data=data,
                          **kwargs)

    # ****************************************************************************************************************
    # **     ConfigManager Magic Methods
    # ****************************************************************************************************************

    def __getitem__(self, key):
        """
        returns a section or option value
        :param str key:
        """
        if self._no_sections:
            return self._sections[self._no_section_section_name][key]

        section, option = self._xf(key)

        try:
            if option is _UNSET:
                return self._sections[section]
            else:
                return self._sections[section][option]
        except KeyError:
            raise NoSectionError(section=section)

    def __setitem__(self, key, value):
        if self._no_sections:
            self._sections[self._no_section_section_name][key] = value
        else:
            section, option = self._xf(key)

            if option is _UNSET:
                if key in self:
                    raise AttributeError('sections may not be edited using this approach')
                else:
                    if isinstance(value, dict):
                        self.add_section(key, **value)
                    else:
                        raise AttributeError('sections added this way must use a dictionary for options')
            else:
                if section not in self:
                    self.add_section(section)

                self[section][option] = value

    def __contains__(self, key):
        if self._no_sections:
            return key in self._sections[self._no_section_section_name]

        section, option = self._xf(key)

        if option is _UNSET:
            return section in self._sections
        else:
            try:
                return option in self._sections[section]
            except KeyError:
                raise NoSectionError(section=section)

    def __len__(self):
        if self._no_sections:
            return len(self._sections[self._no_section_section_name])
        else:
            return len(self._sections)

    def __iter__(self):
        if self._no_sections:
            for o in self._sections[self._no_section_section_name]:
                yield o
        else:
            for k, s in self._sections.items():
                yield s

    '''
    @staticmethod
    def _convert_to_boolean(value):
        return convert_to_boolean(value)

        # removed
    '''