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

from AdvConfigMgr.config_exceptions import *
from AdvConfigMgr.config_interpolation import Interpolation, NoInterpolation
from AdvConfigMgr.config_types import *
from AdvConfigMgr.config_storage import *
from AdvConfigMgr.config_migrate import ConfigMigrationManager

from collections import OrderedDict as _default_dict, ChainMap as _ChainMap
from AdvConfigMgr.utils import args_handler, convert_to_boolean, make_list, slugify, get_after, get_before
import copy
from distutils.version import StrictVersion, LooseVersion, Version

__all__ = ["NoSectionError", "DuplicateOptionError", "DuplicateSectionError",
           "NoOptionError", "InterpolationError", "InterpolationDepthError",
           "InterpolationSyntaxError", "ParsingError",
           "MissingSectionHeaderError",
           "ConfigParser", "SafeConfigParser", "RawConfigParser",
           "DEFAULTSECT", "MAX_INTERPOLATION_DEPTH"]


class ConfigOption(object):
    def __init__(self, section, name, *args, **kwargs):
        """
        An individual option in the config

        :param ConfigSection section:  A pointer to the ConfigSection object that this is a part of
        :param str name: The name of the config object.  This is transformed by the optionxform method in the main config
            manager.  by default this is converted to lowercase
        :param object default_value: Default= _UNSET the default value for the item. If set to :py:class:`_UNSET` this is
            considered to not have a default.  (this allows None to be a valid default setting.
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
        :param bool keep_if_empty: Default=True: If set to False the option will be deleted when the value is cleared AND
            there is no set default value.
        :param bool do_not_change: Default=False If set to True, this will not allow the user to change the option after
            initial loading.
        :param bool do_not_delete: Default=False  If set to True, this will not allow the user to delete the option.
        :param bool required_after_load: Default = False, If set to true, the app should not start without this being set.
            if there is a CLI_option available, the app should prompt the user for that option, if not, the app should
            fail with a usefull message.
        :param bool autoconvert: will attempt to autoconvert values to the datatype, this can be disabled if needed.
            (some types of data may not autoconvert correctly.)
        """
        self._section = section
        self._name = self.section.manager.optionxform(name)

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

        self._value = _UNSET
        self._name = self.section.manager.optionxform(self._name)

        if self.datatype is None:
            if self.default_value is not _UNSET:
                self.datatype = self.default_value.__class__.__name__
            else:
                self.datatype = 'str'

        self._datatype_manager = data_type_generator(self.datatype)(self.validations)
        self._validator = data_type_generator(self.datatype)(self.validations)

        if self.verbose_name is None:
            self.verbose_name = self._name.title()
        if self.do_not_change and self.is_empty:
            raise NoOptionError(self.name, self.section.name)

        if self.cli_options is not None:
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
            self.section._register_cli(self)

        ip.debug('create option: ', self._repr_str)

    @property
    def section(self):
        return self._section

    @property
    def path(self):
        return self.section.name + '.' + self.name

    def validated(self, value):
        return self._datatype_manager(value)

    @property
    def is_empty(self):
        return self.default_value == _UNSET and self._value == _UNSET

    @property
    def can_delete(self):
        tmp_ret = (self.default_value == _UNSET) and (not self.do_not_delete)
        ip.debug('check delete [', self.path, ']').a()
        ip.debug('default_value: ', self.default_value)
        ip.debug('do_not_delete: ', self.do_not_delete)
        ip.debug('can_delete: ', tmp_ret)

        return tmp_ret

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
        raise EmptyOptionError(self.name, self.section.name)

    @property
    def has_cli(self):
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
            self.section.delete(self.name, force=True)

    def delete(self):
        return self.section.delete(self.name)

    def _get(self, interpolater=None, as_string=False):
        """
        internal use get, assumes that if interpolator is None, no interpolation (this is different from .get in that
        .get will set the default interpolater unless raw = True
        :param interpolater:
        :param as_string:
        :return:
        """
        tmp_value = copy.deepcopy(self.value)

        if as_string:
            tmp_value = self._datatype_manager.to_string(tmp_value)

        if interpolater is not None:
            tmp_value = interpolater(self.section.manager, self.section.name, tmp_value)

        ip.debug('get option [', self.path, '], returning ', tmp_value)

        return tmp_value

    def get(self, raw=False, interpolater=None):
        """
        Gets the current value or default interpolated value.

        :param raw: if set to True will bypass the interpolater
        :param interpolater: can be used to override the default interpolater if needed.
        :return: the interpolated value or default value.
        """
        if raw:
            return self._get()

        if interpolater is None:
            interpolater = self.section.manager._interpolation.before_get
        else:
            interpolater = interpolater.before_get

        return self._get(interpolater)

    def to_write(self, raw=False, interpolater=None, as_string=False):
        """
        gets data from the system to save to a storage module,

        :param raw: if set to True will bypass the interpolater
        :param interpolater: can be used to override the default interpolater if needed.
        :return: the interpolated value or default value.
        :param as_string: returns the value as a strong (passing through the datatype module to_string method)
        :return: the interpolated value or default value.
        """
        if raw:
            return self._get(as_string=as_string)

        if interpolater is None:
            interpolater = self.section.manager._interpolation.before_write
        else:
            interpolater = interpolater.before_write

        return self._get(interpolater=interpolater, as_string=as_string)

    def _set(self, value, interpolater=None, validate=True, force=False, from_string=False):
        """
        internal use set, assumes that if interpolator is None, no interpolation (this is different from .get in that
        .get will set the default interpolater unless raw = True

        :param interpolater:
        :param validate:
        :param force: will skip lock checks
        :param from_string: will force conversion from string
        :return:
        """

        if self.autoconvert:
            value = self._datatype_manager.auto_convert(value)
        elif from_string:
            value = self._datatype_manager.from_string(value)

        if interpolater is not None:
            value = interpolater(self.section.manager, self.section.name, value)

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
                if self.section.manager._raise_error_on_locked_edit:
                    raise ForbiddenActionError('Change attempted on locked option [%s]' % self.name)
                ip.debug('option [', self.path, '], is locked')

        else:
            ip.debug('option [', self.path, '], already set to ', value)

        return value

    def set(self, value, raw=False, interpolater=None, validate=True, force=False):
        """
        Sets the current value.

        :param value: the value to set
        :param raw: if set to True will bypass the interpolater
        :param interpolater: can be used to override the default interpolater if needed.
        :param validate: if False will bypass the validation steps
        :param force: if True will bypass the lock checks
        :return: the interpolated value or default value.
        """

        if raw:
            return self._set(value, validate=validate, force=force)

        if interpolater is None:
            interpolater = self.section.manager._interpolation.before_set
        else:
            interpolater = interpolater.before_set

        return self._set(value, interpolater=interpolater, validate=validate, force=force)

    def from_read(self, value, raw=False, interpolater=None, validate=True, from_string=False):
        """
        adds data from a storage module to the system, this ignores the 'do_not_add' flag.

        :param value: the value to add
        :param raw: if set to True will bypass the interpolater
        :param interpolater: can be used to override the default interpolater if needed.
        :param validate: if False will bypass the validation steps
        :param from_string: if True will convert from string
        :return: the interpolated value or default value.
        """

        if raw:
            return self._set(value, validate=validate, force=True, from_string=from_string)

        if interpolater is None:
            interpolater = self.section.manager._interpolation.before_read
        else:
            interpolater = interpolater.before_read

        return self._set(value, interpolater=interpolater, validate=validate, force=True, from_string=from_string)

    def __len__(self):
        return len(self.value)

    def __call__(self, *args):
        if args:
            self.set(args[0])
        return self.get()

    def __contains__(self, item):
        return item in self.options

    def __str__(self):
        return self.name

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
                 option_defaults=None,
                 dict_type=_default_dict,
                 cli_section_title=None,
                 cli_section_desc=None,
                 version=None,
                 version_option_name=None,
                 version_migrations=None):
        """
        :param ConfigManager manager: A pointer to the config manager
        :param str name: The name of the section
        :param str verbose_name: The verbose name of the section
        :param str description: A long description of the section
        :param str storage_write_to: The tag of the storage location to save to, if None, the section will be saved to
            the default location, if '-' it will not be saved in save_all operations, if "*", section will be saved to
            all configured storage locations. Sections can be saved manually to any storage if needed.
        :param str or list storage_read_from_only: options from storage with tags in this list will be read.  If None
            (default) then options in storage will be always be used.  This allows restricting options to specific
            storage locations.
            CLI options, if configured, will always overwrite data from storage.
        :param bool store_default: store defaults in storage medium
        :param bool locked: if True, do not allow any changes to the section
        :param dict_type: the dictionary type to be used.
        :param str cli_section_title: the name of the section in the CLI (if sectioned), Defaults to verbose_name
        :param str cli_section_desc: the description for the section in the CLI (if sectioned), Defaults to description
        :param str version: the version number of the section, if None, this will take the version number of the
            ConfigManager object.
        :param str version_option_name: allows for overriding the ConfigManager's version_option_name setting.
        """

        self._manager = manager
        self._name = manager.sectionxform(name)
        if verbose_name is None:
            self.verbose_name = name.title()
        else:
            self.verbose_name = verbose_name
        self.description = description
        self.storage_write_to = storage_write_to
        self.storage_read_from_only = storage_read_from_only
        self.store_default = store_default
        self.allow_create_on_load = allow_create_on_load
        self.locked = locked
        if option_defaults:
            self.option_defaults = option_defaults
        else:
            self.option_defaults = {}
        self._options = dict_type()
        self.dict_type = dict_type()
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
            if self.manager.version is None:
                if self.manager._enforce_versioning:
                    raise AttributeError('Versioning is required, but no version found')
            else:
                self.version = self.manager.version
        else:
            self.version = self.manager._version_class(version)

        if version_option_name is None:
            self._version_option_name = self.manager._version_option_name.format(section=self.name)
        else:
            self._version_option_name = version_option_name.format(section=self.name)

        if self.version is not None:
            tmp_version_dict = {'name': self._version_option_name,
                                'default_value': self.version,
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

    def _optionxform(self, optionstr):
        return self._manager.optionxform(optionstr)

    def get(self, option, fallback=_UNSET, raw=False, interpolater=None):
        """
        gets the value of an option

        :param option: the name of the option
        :param fallback: a value to return if the option is empty
        :param raw: a flag to skip interpolation
        :param interpolater: the interpolator to use if not the standard one.
        :return:
        """
        option = self._manager.optionxform(option)
        try:
            return self.options[option].get(raw=raw, interpolater=interpolater)
        except KeyError:
            if fallback == _UNSET:
                raise NoOptionError(option, self.name)
            else:
                return fallback

    def set(self, option, value, raw=False, interpolater=None, validate=True, force=False):
        """
        Sets an option value.

        :param option: the name of the option to set
        :param value: the value to set
        :param raw: if set to True will bypass the interpolater
        :param interpolater: can be used to override the default interpolater if needed.
        :param validate: if False will bypass the validation steps
        :param force: if True will bypass the lock checks
        :return: the interpolated value or default value.
        """

        option = self._optionxform(option)

        if option not in self:
            raise NoOptionError(option, self.name)

        if not self.locked or force:
            self.options[option].set(value,
                                     raw=raw,
                                     interpolater=interpolater,
                                     validate=validate,
                                     force=force)

    def from_read(self, option, value, raw=False, interpolater=None, validate=True):
        """
        adds data from a storage module to the system, this ignores the 'do_not_add' flag.

        :param value: the value to add
        :param raw:
        :param interpolater:
        :param as_string:
        :return:
        """

        option = self._optionxform(option)

        try:
            self.options[option].from_read(value,
                                           raw=raw,
                                           interpolater=interpolater,
                                           validate=validate,
                                           force=True)

        except NoOptionError:
            if self.allow_create_on_load:
                self.add(option)
                self.options[option].from_read(value,
                                               raw=raw,
                                               interpolater=interpolater,
                                               validate=validate,
                                               force=True)

            else:
                raise NoOptionError(self.name, option)

    def to_write(self, option, raw=False, interpolater=None, as_string=False):
        """
        gets data from the system to save to a storage module
        :param raw:
        :param interpolater:
        :param as_string:
        :return:
        """
        option = self.manager.optionxform(option)
        return self.options[option].to_write(raw=raw, interpolater=interpolater, as_string=as_string)

    def item(self, option_name):
        return self._options[option_name]

    def items(self, raw=False, interpolater=None):
        """
        Return a list of (name, value) tuples for each option in a section.

        All interpolations are expanded in the return values, based on the
        defaults passed into the constructor, unless the optional argument
        'raw' is true.
        """
        tmp_items = list(self.options)
        tmp_ret = []
        for i in tmp_items:
            tmp_ret.append((i, self.get(i, raw=raw, interpolater=interpolater)))

        return tmp_ret

    def delete(self, option, force=False, forgiving=False):
        """
        Will delete a list of options.

        :param option: Option name or list of option names.
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

        option = make_list(option)
        ip.debug('delete options: ', option)
        self.last_failure_list = []
        tmp_ret = True
        for o in option:
            ip.debug('trying option: ', o)

            try:
                opt = self.options[self._optionxform(o)]
                if opt.has_default_value and not force:
                    ip.debug('section ', self._name, ' delete-clearing option ', o)
                    opt.clear()
                elif not opt.do_not_delete or force:
                    ip.debug('section ', self._name, ' deleteing option ', o)
                    del self.options[self._optionxform(o)]
                else:
                    ip.debug('option ', o, ' delete prohibited')
                    self.last_failure_list.append(o)
                    tmp_ret = False
            except KeyError:
                ip.debug('option ', o, ' not found ')
                if forgiving:
                    self.last_failure_list.append(o)
                    tmp_ret = False
                else:
                    raise NoOptionError(o)
        return tmp_ret

    def clear(self, option, forgiving=False):
        """
        Will set the option to the default value or to unset as long as long as the section is not locked.

        :param option: option name or list of option names
        :type option: str or list
        :param bool forgiving: True will return False if the option is not found, False, will raise NoOptionError.
        :return: True if all deletes passed, False if not.  if False, a list of the failed options is stored in
            self.last_failure_list
        :rtype: bool
        :raises NoOptionError: If the option does not exist. and forgiving is False.
        """
        if self.locked:
            ip.debug('section ', self._name, ' locked ')
            self.last_failure_list.extend(make_list(option))
            return False

        option = make_list(option)
        self.last_failure_list = []
        tmp_ret = True
        for o in option:
            ip.debug('trying option: ', o)
            try:
                ip.debug('section ', self._name, ' clearing option ', o)
                self.options[self._optionxform(o)].clear()
            except KeyError:
                ip.debug('option ', o, ' not found ')
                if forgiving:
                    self.last_failure_list.append(o)
                    tmp_ret = False
                else:
                    raise NoOptionError(o)
        return tmp_ret


    '''
    def get_subset(self, filter_for=_UNSET, filter_field='name', filter_type='eq'):
        for ret in self._filter(filter_for, filter_field, filter_type):
            yield ret
    '''

    def _register_cli(self, option):
        if self.manager._cli_parser_name is not None:
            self.manager.storage.get(self.manager._cli_parser_name).reset_cache()
            tmp_args = option.cli_options
            tmp_dest = option.cli_options['dest']
            tmp_flags = make_list(tmp_args['flags'])
            for f in tmp_flags:
                if f in self.manager._cli_flags:
                    raise DuplicateCLIOptionError(option.name, f)
                self.manager._cli_flags.append(f)

            self._cli_args[tmp_dest] = tmp_args
            self.manager._cli_args[tmp_dest] = option


    def defaults(self):
        """
        returns a dictionary of the default settings
        :return:
        """
        tmp_ret = copy.copy(self.dict_type)
        for name, rec in self.options.values():
            if rec.has_default_value:
                tmp_ret[name] = rec
        return tmp_ret

    def load(self, name, value, *args, **kwargs):
        """
        Loads value into system, can create new options if "allow_create_on_load" is set.

        :param name: Option Name
        :param value: Option Value
        :param args: as per ConfigOptionClass (passed through)
        :param kwargs: as per ConfigOptionClass (passed through)
        """
        if name not in self:
            if not self.allow_create_on_load:
                raise NoOptionError

            kwargs['datatype'] = value.__class__.__name__

            self._add(name, *args, force_load=True, **kwargs)

        self.set(name, value)

    @property
    def options_list(self):
        return list(self.options.keys())

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
                    self._add(name, **o)
                except KeyError:
                    raise AttributeError('config parameter dict does not contain "name"')
            elif isinstance(o, str):
                self._add(o)

    def _add(self, name, *args, **kwargs):
        """
        Adds new option definition to the system
        :param name: option name
        :param args: as per ConfigOptionClass (passed through)
        :param kwargs: as per ConfigOptionClass (passed through)
        :return:
        """
        with_defaults = copy.copy(self.option_defaults)
        with_defaults.update(kwargs)
        if self.locked:
            kwargs['do_not_change'] = True
            kwargs['do_not_delete'] = True

        self._options[name] = ConfigOption(self, name, *args, **with_defaults)

    @property
    def options(self):
        return self._options

    @property
    def manager(self):
        # The parser object of the proxy is read-only.
        return self._manager

    @property
    def name(self):
        # The name of the section on a proxy is read-only.
        return self._name

    def __repr__(self):
        return 'ConfigSection: {}'.format(self._name)

    def __getitem__(self, key):
        if self.manager._section_option_sep is not None and self.manager._section_option_sep in key:
            return self.manager[key]
        else:
            return self.get(key)

    def __setitem__(self, option, value):
        """ sets item value """
        if self.manager._section_option_sep is not None and self.manager._section_option_sep in option:
            self.manager[option] = value
        else:
            self.set(option, value)

    def __delitem__(self, key):
        return self.delete(key)

    def __contains__(self, key):
        if self.manager._section_option_sep is not None and self.manager._section_option_sep in key:
            return key in self.manager
        else:
            return self._optionxform(key) in self.options

    def __len__(self):
        return len(self.options)

    def __iter__(self):
        for key, opt in self.options.items():
            yield opt


class ConfigManager(object):
    # Interpolation algorithm to be used if the user does not specify another
    _DEFAULT_INTERPOLATION = Interpolation()
    _DEFAULT_SECT_NAME = "__DEFAULT__"

    # ******************** Finish items ***************************
    #: TODO: implement allow no value
    #: TODO: implement upgrade/downgrade functions
    #: TODO: Document system.

    def __init__(self,
                 name='Configuration',
                 # dict_type=_default_dict,
                 allow_no_value=False,
                 *,
                 empty_lines_in_values=True,
                 allow_add_from_storage=True,
                 no_sections=False,
                 section_defaults=None,
                 interpolation=_UNSET,
                 section_option_sep='.',
                 cli_program=None,
                 cli_desc=None,
                 cli_epilog=None,
                 cli_group_by_section=True,
                 cli_parser_name='cli',
                 raise_error_on_locked_edit=False,
                 storage_managers=None,
                 version_class=None,
                 version=None,
                 version_option_name='{section}_version_number',
                 version_allow_unversioned=True,
                 version_enforce_versioning=False,
                 version_disable_cross_section_copy=False,
                 version_migrations=None,
                 **kwargs
                 ):
        """
        :param allow_no_value: allow empty values.
        :param empty_lines_in_values:
        :param allow_add_from_storage: allow adding sections and options directly from the storage
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

        self.last_fail_list = []
        self._name = name
        self._dict = _default_dict
        self._sections = self._dict()
        self._allow_no_value = allow_no_value
        self._allow_add_from_storage = allow_add_from_storage
        self._empty_lines_in_values = empty_lines_in_values
        self._no_sections = no_sections
        self._interpolation = interpolation
        self._cli_parser_args = {'prog': cli_program, 'description': cli_desc, 'epilog': cli_epilog}
        self._raise_error_on_locked_edit = raise_error_on_locked_edit
        self._allow_unversioned = version_allow_unversioned
        self._enforce_versioning = version_enforce_versioning

        self._version_option_name = version_option_name

        if self._no_sections:
            self._cli_group_by_section = False
            self._version_disable_cross_section_copy = True
            self._section_option_sep = None

        else:
            self._cli_group_by_section = cli_group_by_section
            self._version_disable_cross_section_copy = version_disable_cross_section_copy
            self._section_option_sep = section_option_sep

        if version_class is None:
            self._version_class = LooseVersion
        else:
            if isinstance(version_class, str):
                if version_class == 'loose':
                    self._version_class = LooseVersion
                elif version_class == 'strict':
                    self._version_class = StrictVersion
                else:
                    raise AttributeError('Invalid version class passed')
            else:
                self._version_class = version_class

        if version is not None:
            ip.debug('Version is not None, setting version to: ', version)
            self._version = self._version_class(version)
        else:
            self._version = None

        if section_defaults:
            self.section_defaults = section_defaults
        else:
            self.section_defaults = {}

        if interpolation is _UNSET:
            self._interpolation = self._DEFAULT_INTERPOLATION
        elif interpolation is None:
            self._interpolation = NoInterpolation(sep=self._section_option_sep)
        else:
            self._interpolation = interpolation(sep=self._section_option_sep)

        self._cli_flags = []
        self._cli_args = {}
        self._cli_parser_name = cli_parser_name
        if storage_managers:
            self._storage = StorageManagerManager(self, *storage_managers, cli_parser_name=cli_parser_name)
        else:
            self._storage = StorageManagerManager(self, cli_parser_name=cli_parser_name)

        # self._cli_parser = None

        if self._no_sections:
            self.add_section(self._DEFAULT_SECT_NAME, force_add_default=True, **kwargs)

        if version_migrations is None:
            self._migrations = []
        else:
            self._migrations = version_migrations

    @property
    def version(self):
        return self._version

    @property
    def name(self):
        return self._name

    def sections(self):
        """Return a list of section names"""
        return list(self._sections.keys())

    def get_sec_migrations(self, section):
        tmp_ret = []
        for m in self._migrations:
            tmp_section = self.sectionxform(m['section_name'])
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

    def add_section(self, section, force_add_default=False, **kwargs):
        """Create a new section in the configuration.

        Raise DuplicateSectionError if a section by the specified name
        already exists.
        """
        if self._no_sections and not force_add_default:
            raise SimpleConfigError(section)

        section = self.sectionxform(section)

        options = kwargs.pop('options', None)
        kwargs['version_migrations'] = self.get_sec_migrations(section)

        if section in self._sections:
            raise DuplicateSectionError(section)

        with_defaults = copy.copy(self.section_defaults)
        with_defaults.update(kwargs)

        self._sections[section] = ConfigSection(self, section, **with_defaults)

        if options is not None:
            self[section].add(options)

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
            return self._sections[self._DEFAULT_SECT_NAME].add(*args, **kwargs)

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

    def has_section(self, section):
        """Indicate whether the named section is present in the configuration.
        """
        if self._no_sections:
            raise SimpleConfigError(section)

        return self.sectionxform(section) in self._sections

    '''
    @property
    def cli_parser(self):
        if self._cli_parser is None:
            ip.debug('Creating CLI Parser').a()
            self._cli_parser = ArgumentParser(**self._cli_parser_args)
            cli_sect = self._cli_parser

            for s in self:
                if self._cli_group_by_section and s._cli_args:
                    ip.debug('creating CLI section: ', s._cli_section_options['title'])
                    cli_sect = self._cli_parser.add_argument_group(**s._cli_section_options)

                for d, o in s._cli_args.items():
                    tmp_args = copy.copy(o)
                    tmp_flags = tmp_args.pop('flags')
                    ip.debug('creating CLI argument "', tmp_flags, '" with options ', tmp_args)
                    cli_sect.add_argument(*tmp_flags, **tmp_args)
        ip.s()
        return self._cli_parser

    def parse_cli(self, args=None):
        """
        will parse any cli arguments based on the configuration settings
        :param args: a list of arguments can be passed in which case the method will parse the list instead of
            sys.args()
        """
        ip.debug('Parsing CLI arguments: ', args)
        tmp_args = vars(self.cli_parser.parse_args(args))

        for dest, value in tmp_args.items():
            self._cli_args[dest].from_read(value, from_string=True)
    '''

    def optionxform(self, optionstr, extra_allowed='_'):
        """
        Will transform the option name string as needed, by default this will slugify and lowercase the string.

        This can be overridden as desired.
        """
        return slugify(optionstr, extra_allowed, 'lower', punct_replace='_')

    def sectionxform(self, sectionstr, extra_allowed='_'):
        """
        Will transform the section name string as needed, by default this will slugify and uppercase the string.

        This can be overridden as desired.
        """
        return slugify(sectionstr, extra_allowed, 'upper', punct_replace='_')

    # ****************************************************************************************************************
    # **                Storage Methods
    # ****************************************************************************************************************

    @property
    def storage(self):
        return self._storage

    def write(self, sections=None, storage_names=None, override_tags=False):
        """
        runs the write to storage process for the selected or configured managers

        :param storage_name: If None, will write to all starnard storage managers, if a string or list, will write to the
            selected ones following the configured tag settings.
        :param sections: If None, will write to all sections, if string or list, will write to the selected ones
            following the configured tag settings.
        :param override_tags: if True, this will override the configured storage tag settings allowing things like
            exporting the full config etc.
        :return: if ONLY one storage_tag is passed, this will return the data from that manager if present.
        """
        return self.storage.write(sections=sections, storage_names=storage_names, override_tags=override_tags)

    def read(self, sections=None, storage_names=None, override_tags=False, data=None):
        """
        runs the read from storage process for the selected or configured managers

        :param storage_name: If None, will read from all starnard storage managers, if a string or list, will read from
            the selected ones following the configured tag settings.
        :param sections: If None, will read from all sections, if string or list, will read from the selected ones
            following the configured tag settings.
        :param override_tags: if True, this will override the configured storage tag settings allowing things like
            exporting the full config etc.
        :param data: if a single storage tag is passed, then data can be passed to that storage manager for saving.
            this will raise an AssignmentError if data is not None and more than one storage tag is passed.
        """
        self.storage.read(sections=sections, storage_names=storage_names, override_tags=override_tags, data=data)

    """
    def read(self, filenames, encoding=None):
    def read_file(self, f, source=None):
    def read_string(self, string, source='<string>'):
    def read_dict(self, dictionary, source='<dict>'):
    def readfp(self, fp, filename=None):
    def write(self, fp, space_around_delimiters=True):
    def _write_section(self, fp, section_name, section_items, delimiter):
    """

    # removed
    '''
    def remove_option(self, section, option):
        """Remove an option."""
        if not section or section == self.default_section:
            sectdict = self._defaults
        else:
            try:
                sectdict = self._sections[section]
            except KeyError:
                raise NoSectionError(section)
        option = self.optionxform(option)
        existed = option in sectdict
        if existed:
            del sectdict[option]
        return existed
    '''

    # removed
    '''

    def remove_section(self, section):
        """Remove a file section."""
        existed = section in self._sections
        if existed:
            del self._sections[section]
            del self._proxies[section]
        return existed
    '''

    # fixed
    def __getitem__(self, key):
        """
        returns a section object
        :param key:
        :rtype ConfigSection:
        """

        if self._no_sections:
            return self._sections[self._DEFAULT_SECT_NAME][key]

        elif self._section_option_sep is not None and self._section_option_sep in key:
            sec_key = self.sectionxform(get_before(key, self._section_option_sep))
            opt_key = self.optionxform(get_after(key, self._section_option_sep))

            try:
                return self._sections[sec_key][opt_key]
            except KeyError:
                raise NoSectionError(key)

        else:
            try:
                return self._sections[self.sectionxform(key)]
            except KeyError:
                raise NoSectionError(key)

    def __setitem__(self, key, value):
        if self._no_sections:
            self._sections[self._DEFAULT_SECT_NAME][key] = value

        elif self._section_option_sep is not None and self._section_option_sep in key:
            sec_key = self.sectionxform(get_before(key, self._section_option_sep))
            opt_key = self.optionxform(get_after(key, self._section_option_sep))

            if sec_key not in self:
                self.add_section(sec_key)

            self[sec_key][opt_key] = value

        else:
            if key not in self:
                if isinstance(value, dict):
                    raise ValueError('sections added this way must use a dictionary for options')
                self.add_section(key, **value)
            else:
                raise AttributeError('sections may not be edited using this approach')

    def __contains__(self, key):
        if self._no_sections:
            return key in self._sections[self._DEFAULT_SECT_NAME]

        elif self._section_option_sep is not None and self._section_option_sep in key:
            sec_key = get_before(key, self._section_option_sep)
            opt_key = self.optionxform(get_after(key, self._section_option_sep))

            if self.has_section(sec_key) in self and opt_key in self[sec_key]:
                return True
            else:
                return False
        else:
            return self.has_section(key)

    def __len__(self):
        if self._no_sections:
            return len(self._sections[self._DEFAULT_SECT_NAME])
        else:
            return len(self._sections)

    def __iter__(self):
        if self._no_sections:
            for o in self._sections[self._DEFAULT_SECT_NAME]:
                yield o
        else:
            for k, s in self._sections.items():
                yield s

    @staticmethod
    def _convert_to_boolean(value):
        return convert_to_boolean(value)

        # removed
