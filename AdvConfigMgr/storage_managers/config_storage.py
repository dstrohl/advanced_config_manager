__author__ = 'dstrohl'

from AdvConfigMgr.config_exceptions import *
from AdvConfigMgr.utils import make_list, merge_dictionaries
from AdvConfigMgr.utils.filehandler import PathHandler
from argparse import ArgumentParser
import copy
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

__all__ = ['BaseConfigStorageManager', 'StorageManagerManager', 'ConfigCLIStorage', 'ConfigSimpleDictStorage',
           'ConfigFileStorage', 'ConfigStringStorage', 'BaseConfigRecordBasedStorageManager']


class BaseConfigStorageManager(object):
    """
    Base class for storage managers, defines an expandable storage subsystem for configs.

    Also, the two methods; BaseConfigStorageManager.read() and BaseConfigStorageManager.write() need to be overwritten
    to read and write the data in the format needed.

    if the manager is intended to be a 'standard' one, in other words, if it will be used for automatic
    read-all/write-all processes, it must be able to run without passing any data or arguments, all configuration
    must be done during initialization.  if it will only be used standalone or on-demand, you can allow any information
    to be passed.

    """

    """:param str storage_type_name: This is the name of the manager class, it is used in log entries and
        potentially UI's."""
    storage_type_name = 'Base'

    """:param str storage_name: The internal name of the storage manager, must be unique"""
    storage_name = None

    """
    :param bool force_strings: If True, the system will convert all options to strings before writing to the manager,
        and from strings when reading from it.

    """
    force_strings = False

    """:param bool standard:  True if this should be used for read_all or write_all ops"""
    standard = True

    """:param bool allow_create: True if this can create options in the system, even if they are not pre-configured."""
    allow_create = True

    """:param bool force: True if this will set options even if they are locked"""
    force = False

    """:param bool overwrite: True if this will overwrite options that have existing values"""
    overwrite = True

    """:param bool lock_after_read: True if this will lock the option after reading"""
    lock_after_read = False

    """:param int priority: the priority of this manager, with smallest being run earlier than larger."""
    priority = 100

    def __init__(self):
        """

        """

        """:type self.manager: AdvConfigMgr.advconfigmgr.ConfigManager  """
        self.manager = None  # this is set during registration.

        self._flat_dict = None

        self.last_section_count = 0
        self.last_option_count = 0

        self.data = None

        ip.info('Loading storage manager: ', self.storage_name)

    def config(self, config_dict):
        """
        :param config_dict: a dictionary with storage specific configuration options., this is called after the storage
            manager is loaded.
        """
        self.priority = config_dict.get('priority', self.priority)

        self.storage_type_name = config_dict.get('storage_type_name', self.storage_type_name)
        self.storage_name = config_dict.get('storage_name', self.storage_name)
        self.force_strings = config_dict.get('force_strings', self.force_strings)
        self.standard = config_dict.get('standard', self.standard)
        self.allow_create = config_dict.get('allow_create', self.allow_create)
        self.force = config_dict.get('force', self.force)
        self.overwrite = config_dict.get('overwrite', self.overwrite)
        self.lock_after_read = config_dict.get('lock_after_read', self.lock_after_read)

    def read(self, section_name=None, storage_name=storage_name, **kwargs):
        """
        Read from storage and save to the system

        :param section_name: A string or list of sections to read from in the config.
        :type section_name: str or list
        :param str storage_name: A string name of the storage manager, this can be used to override the configured name.
        :param kwargs: each storage manager may define its own additional args, but must also implement the final
            kwargs parameter so that if it is called with other arguments, it wont cause an error.
        :return: the number of sections / options added

        The recommended implementation method us to read from your storage method (database, special file, etc) and
        store the arguments in a dictionary or dictionary of dictionaries.  then pass that dict
        to :py:meth:`BaseConfigStorageManager._save_dict`.  that method will take care of writing the data, converting
        it if needed, making sure that it is allowed to write, handling locked sections and options, etc...

        if the implementation tries to pass data directly to the file manager for importing, it will save the data in
        :py:meth:`BaseConfigStorageManager.data` where you can read it, so you should check this before processing.

        You should keep track of the number of sections and options written/read and return these at the end::

            return self.last_section_count, self.last_option_count
        """
        raise NotImplementedError

    def write(self, section_name=None, storage_name=storage_name, **kwargs):
        """
        Write data from the system and save to your storage

        :param section_name: A string or list of sections to write to.
        :type section_name: str or list
        :param str storage_name: A string name of the storage manager, this can be used to override the configured name.
        :param kwargs: each storage manager may define its own additional args, but must also implement the final
            kwargs parameter so that if it is called with other arguments, it wont cause an error.
        :return: the number of sections / options written

        The recommended implementation method is to call :py:meth:`BaseConfigStorageManager._get_dict` which will return
        a dictionary of the options or dictionary of sections (which are dicts of options) to be saved.  You can then
        iterate through these and save them in your storage system.

        if you want to return data direct from the write method, you should copy it
        to :py:meth:`BaseConfigStorageManager.data` after processing.

        you should keep track of the number of sections and options written/read and return these at the end::

            return self.last_section_count, self.last_option_count
        """
        raise NotImplementedError

    @property
    def is_default(self):
        return self.manager.storage.default_manager.storage_name == self.storage_name

    def _ok_to_read_section(self, section_name, storage_name=storage_name):
        ip.debug('checking for OK to READ section, ', section_name, ' with storage ', storage_name)
        if section_name not in self.manager:
            if self.allow_create and self.manager.allow_create_from_storage:
                self.manager.add_section(dict(name=section_name, storage_write_to=self.storage_name))
                ip.a().debug('YES').s()
                return True
            else:
                ip.a().debug('NO: section name not valid').s()
                return False
        if storage_name == '*':
            ip.a().debug('YES').s()
            return True

        tmp_section_tag = self.manager[section_name].storage_read_from_only

        if tmp_section_tag is None:
            ip.a().debug('YES').s()
            return True

        if storage_name in list(tmp_section_tag):
            ip.a().debug('YES').s()
            return True

        ip.a().debug('NO: fell through checks.').s()
        return False

    def _ok_to_write_section(self, section_name, storage_name=None):
        ip.debug('checking for OK to WRITE section, ', section_name, ' with storage ', storage_name)

        if storage_name is None:
            storage_name = self.storage_name

        if storage_name == '*':
            ip.a().debug('YES').s()
            return True

        tmp_section_tag = self.manager[section_name].storage_write_to

        if tmp_section_tag is None:
            if self in self.manager.storage.manager_list:
                ip.a().debug('YES').s()
                return True
            else:
                ip.a().debug('NO: section name does not have storage name defined, and storage is not in default.')
                ip.debug('current storage: ', self)
                ip.debug('default list: ', self.manager.storage.manager_list).s()
                return False

        if tmp_section_tag == '*' or tmp_section_tag == storage_name:
            ip.a().debug('YES').s()
            return True

        ip.a().debug('NO: fell through checks.').s()
        return False

    def _get_dict(self, section_name=None, storage_name=storage_name):
        """
        Returns a dictionary of options.

        :param section_name: a string name of a section or list of section names to get to.  if this is a single
            string, it is assumed it is the base of the dictionary and all keys are options, if this is None or if it
            is a tuple/list, it is assumed that the keys of the dictionary are sections, containing dictionaries of
            options.
            If this is None, all sections will be queried based on their storage name.  this does NOT override the
            storage_name.
        :type section_name: str or list or None
        :param str storage_name: allows overriding the storage name
        :return: A dictionary of the options matching the sections and storage names passed.
        :rtype: dict
        """
        ip.debug('storage [', self.storage_name, '] creating a dictionary of options.').push()
        self.last_section_count = 0
        self.last_option_count = 0

        tmp_ret = {}

        if isinstance(section_name, str) or self.manager._no_sections:
            self._flat_dict = True
        else:
            self._flat_dict = False

        if section_name is None:
            section_name = self.manager.sections
        else:
            section_name = make_list(section_name)

        ip.debug('section name parameter: ', section_name)

        for section in self.manager:
            ip.debug('storage [', self.storage_name, '] checking section ', section.name)

            ok_2_get = False
            if section_name == [None] or section.name in section_name:
                ip.debug('storage [', self.storage_name, '] section selectable', section.name)

                if self._ok_to_write_section(section.name, storage_name):
                    ip.debug('storage [', self.storage_name, '] checking allowed ', section.name)
                    if len(section) > 0:
                        ip.debug('storage [', self.storage_name, '] checking has content ', section.name)
                        ok_2_get = True

            if ok_2_get:
                ip.debug('storage [', self.storage_name, '] getting section ', section.name)

                tmp_sec = {}

                self.last_section_count += 1
                for option in section:
                    opt_success, opt_value = self._get_option(section, option)
                    if opt_success:
                        self.last_option_count += 1
                        tmp_sec[option.name] = opt_value

                if self._flat_dict:
                    tmp_ret = tmp_sec
                else:
                    tmp_ret[section.name] = tmp_sec
        ip.debug('returning ', tmp_ret)
        ip.pop()
        return tmp_ret

    def _get_option(self, section, option):
        """
        Assumes that the section is already checked for tag permissions,
        Assumes that the section and option do exist.

        :param section: the section object to get
        :param option: the option object to get
        :return: success, value
            success: [True/False] True if the data was successfully returned
            value: the value to store
        """
        ip.debug('getting option [', option, '] for storage ', self.storage_name).a()

        get_rec = True
        tmp_ret = None
        if not option.has_set_value:
            if not option.has_default_value:
                get_rec = False
            elif not section.store_default:
                get_rec = False

        if get_rec:
            tmp_ret = option.to_write(as_string=self.force_strings)

        ip.s()
        return get_rec, tmp_ret

    def _save_dict(self, dict_in, section_name=None, storage_name=None):
        """
        Takes a dictionary and saves it to the system

        :param dict dict_in: the dictionary to save.
            if a single section name is passed, OR if the config manager is set to simple config (no sections), this
            should be a dictionary of options.  otherwise this should be a dictionary of sections, each a dictionary
            of options.
        :param section_name: a string name of a section or list of section names to save to.  if this is a single
            string, it is assumed it is the base of the dictionary and all keys are options, if this is None, all of the
            sections in the dict will be processed, if it is a tuple/list, then only the sections in the dict that
            match items in the section_name will be processed.
            This does not override the storage names.
        :type section_name: str or list or None
        :param str storage_name: allows overriding the storage name
        """

        if storage_name is None:
            storage_name = self.storage_name

        self.last_section_count = 0
        self.last_option_count = 0
        self.processed_sections = []  # used by the record type storage manager.

        if self.manager._no_sections:
            section_name = self.manager._DEFAULT_SECT_NAME

        if isinstance(section_name, str):
            dict_in = {section_name: dict_in}

        if section_name is not None:
            section_name = make_list(section_name)
        else:
            section_name = self.manager.sections

        for section, options in dict_in.items():
            section, option = self.manager._xf(section)
            if section in section_name:
                if self._ok_to_read_section(section, storage_name):
                    self.processed_sections.append(section)
                    self.last_section_count += 1

                    storage_version = options.get(self.manager[section].version_option_name, None)
                    options = self.manager[section].migrate_dict(storage_version, options)

                    for option, value in options.items():
                        sav_suc = self._set_option(section, option, value)
                        if sav_suc:
                            self.last_option_count += 1

    def _set_option(self, section_name, option_name, value):
        """
        Assumes that the section is already checked for the tag.

        .. note:: if the storage method only stores strings, and this has to create an option, that option will be
            created as a string.
        """
        saved = False
        ip.debug('reading option [', option_name, '] from storage ', self.storage_name).a()
        save_option = True
        section = self.manager[section_name]

        if option_name not in section:
            if not self.allow_create:
                ip.error('option [', option_name, '] does not exist and allow_create is False')
                raise NoOptionError(option_name, section)
            elif section.locked and not self.force:
                ip.error('option [', option_name, '] does not exist and section is locked')
                raise NoOptionError(option_name, section)

            section.add(dict(name=option_name, default_value=value, do_not_change=self.lock_after_read))
            saved = True
        else:
            option_rec = section.item(option_name)
            if option_rec.has_set_value and not self.overwrite:
                ip.warning('option [', option_name, '] has a value and overwrite is False')
                save_option = False
            elif option_rec.do_not_change and not self.force:
                ip.warning('option [', option_name, '] has a is locked and force is False')
                save_option = False

            if save_option:
                option_rec.from_read(value, from_string=self.force_strings)
                option_rec.do_not_change = self.lock_after_read
                saved = True
                ip.debug('option [', option_rec.path, '] updated with: ', option_rec)

        ip.s()
        return saved

    def __repr__(self):
        return self.storage_type_name + ' [' + self.storage_name + ']'


class BaseConfigRecordBasedStorageManager(BaseConfigStorageManager):
    """
    This base method is intended to be used for record based storage managers, when saving options to the system,
    this will also poll the deleted records list and remove them from the database.
    """

    def _save_dict(self, dict_in, section_name=None, storage_name=None):
        self.processed_sections = []

        super(BaseConfigRecordBasedStorageManager, self)._save_dict(dict_in=dict_in,
                                                                    section_name=section_name,
                                                                    storage_name=storage_name)

        for section in self.processed_sections:
            deleted_records = self.manager[section].migration.options_to_remove
            for del_rec in deleted_records:
                self.delete_record(section, del_rec)

    def delete_record(self, section, option):
        """
        This must be implemented for records based storage managers,

        This method takes a section and option, and deletes that record in the database.
        """
        raise NotImplementedError


class ConfigCLIStorage(BaseConfigStorageManager):
    """
    Read configuration from the CLI
    """
    storage_type_name = 'CLI Manager'
    storage_name = 'cli'
    standard = True  #: True if this should be used for read_all/write_all ops
    force_strings = False  #: True if the storage only accepts strings
    force = True  #: True if this will set options even if they are locked
    overwrite = True  #: True if this will overwrite options that have existing values
    lock_after_read = True  #: True if this will lock the option after reading
    priority = 1

    def __init__(self):
        self._reset_config_cache = True
        self._cli_parser = None
        super(ConfigCLIStorage, self).__init__()

    def read(self, section_name=None, storage_name=storage_name, **kwargs):
        """
        will take a dictionary and save it to the system
        :param dict_in:
        :param storage_name:
        :return:
        """

        self._parse_cli(self.data)
        self.data = None

        return self.last_section_count, self.last_option_count

    def write(self, section_name=None, storage_name=storage_name, **kwargs):
        """
        cli does not accept writing options -- disabled
        """
        self.last_section_count = 0
        self.last_option_count = 0
        return self.last_section_count, self.last_option_count

    def reset_cache(self):
        """
        Reloades the cli_parser from the config.
        """
        self._reset_config_cache = True

    @property
    def cli_parser(self):
        if self._cli_parser is None or self._reset_config_cache:
            ip.debug('Creating CLI Parser').a()
            self._cli_parser = ArgumentParser(**self.manager._cli_parser_args)
            cli_sect = self._cli_parser

            for s in self.manager:
                ip.debug('checking for cli options in sections: ', s.name)
                if self.manager._cli_group_by_section and s._cli_args:
                    ip.debug('creating CLI section: ', s._cli_section_options['title'])
                    cli_sect = self._cli_parser.add_argument_group(**s._cli_section_options)

                for d, o in s._cli_args.items():
                    tmp_args = copy.copy(o)
                    tmp_flags = tmp_args.pop('flags')
                    ip.debug('creating CLI argument "', tmp_flags, '" with options ', tmp_args)
                    cli_sect.add_argument(*tmp_flags, **tmp_args)
            self._reset_config_cache = False
        else:
            ip.debug('CLI PARSER FOUND')
        ip.s()
        return self._cli_parser

    def _parse_cli(self, args=None):
        """
        will parse any cli arguments based on the configuration settings
        :param args: a list of arguments can be passed in which case the method will parse the list instead of
            sys.args()
        """
        ip.debug('Parsing CLI arguments: ', args)
        tmp_args = vars(self.cli_parser.parse_args(args))

        for dest, value in tmp_args.items():
            self.last_option_count += 1
            self.manager._cli_args[dest].from_read(value, from_string=True)


class ConfigSimpleDictStorage(BaseConfigStorageManager):
    """Read configuration from a dictionary.

    Keys are section names, values are dictionaries with keys and values
    that should be present in the section.
    """
    storage_type_name = 'Simple Dictionary Storage'
    storage_name = 'dict'
    standard = False  #: True if this should be used for read_all/write_all ops

    def read(self, section_name=None, storage_name=storage_name, **kwargs):
        """
        will take a dictionary and save it to the system
        :param dict_in:
        :param storage_name:
        :return:
        """
        self._save_dict(self.data, section_name, storage_name)
        return self.last_section_count, self.last_option_count

    def write(self, section_name=None, storage_name=storage_name, **kwargs):
        """
        will return a dictionary from the system
        :param storage_name:
        :return:
        """
        self.data = self._get_dict(section_name, storage_name)
        return self.last_section_count, self.last_option_count


class ConfigStringStorage(BaseConfigStorageManager):
    """
    A file manager that returns or saves configuration in the format of a string of list. in a text file

    this manager handles strings formatted as a standard INI file, or lists of strings formatted that way.

    :param tuple delimiters: the delimiter between the key and the value
    :param tuple comment_prefixes:  this is a tuple of characters that if they occur as the first non-whitespace
        character of a line, the line is a comment
    :param tuple inline_comment_prefixes: this is a tuple of characters that if they occur elsewhere in the line after a
        whitespace char, the rest of the line is a comment.
    :param bool space_around_delimiters: True if space should be added around the delimeters.
    :param bool strict: if False, duplicate sections will be merged, if True, duplicate sections will raise an error
    """

    _delimiters = ('=', ':')
    _comment_prefixes = ('#', ';')
    _inline_comment_prefixes = set()
    _space_around_delimiters = True
    _strict = True

    storage_type_name = 'INI String'
    storage_name = 'string'  #: the internal name of the storage manager, must be unique
    force_strings = True  #: True if the storage only accepts strings

    # Regular expressions for parsing section headers and options
    _SECT_TMPL = r"""
        \[                                 # [
        (?P<header>[^]]+)                  # very permissive!
        \]                                 # ]
        """
    _OPT_TMPL = r"""
        (?P<option>.*?)                    # very permissive!
        \s*(?P<vi>{delim})\s*              # any number of space/tab,
                                           # followed by any of the
                                           # allowed delimiters,
                                           # followed by any space/tab
        (?P<value>.*)$                     # everything up to eol
        """
    _OPT_NV_TMPL = r"""
        (?P<option>.*?)                    # very permissive!
        \s*(?:                             # any number of space/tab,
        (?P<vi>{delim})\s*                 # optionally followed by
                                           # any of the allowed
                                           # delimiters, followed by any
                                           # space/tab
        (?P<value>.*))?$                   # everything up to eol
        """
    # Compiled regular expression for matching sections
    SECTCRE = re.compile(_SECT_TMPL, re.VERBOSE)

    # Compiled regular expression for matching options with typical separators
    OPTCRE = re.compile(_OPT_TMPL.format(delim="=|:"), re.VERBOSE)

    # Compiled regular expression for matching options with optional values
    # delimited using typical separators
    OPTCRE_NV = re.compile(_OPT_NV_TMPL.format(delim="=|:"), re.VERBOSE)

    # Compiled regular expression for matching leading whitespace in a line
    NONSPACECRE = re.compile(r"\S")

    # Possible boolean values in the configuration.
    BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True,
                      '0': False, 'no': False, 'false': False, 'off': False}

    def __init__(self):

        if self._delimiters == ('=', ':'):
            self._optcre = self.OPTCRE_NV
        else:
            d = "|".join(re.escape(d) for d in self._delimiters)
            self._optcre = re.compile(self._OPT_NV_TMPL.format(delim=d), re.VERBOSE)

        super(ConfigStringStorage, self).__init__()

    def read(self, section_name=None, storage_name=storage_name, **kwargs):
        """
        will read an ini file and save it to the system

        :param section_name:
        :type section_name: str or list
        :param str storage_name:
        :return:
        :rtype: int
        """

        if isinstance(self.data, str):
            self.data = self.data.splitlines()

        out_dict = self._parse_list(self.data, 'passed_string')

        self._save_dict(out_dict, section_name, storage_name)
        self.data = None

        return self.last_section_count, self.last_option_count

    def _parse_list(self, list_in, filename):
        """
        Parse a sectioned list from a config file.

        Each section in a configuration file contains a header, indicated by
        a name in square brackets (`[]'), plus key/value options, indicated by
        `name' and `value' delimited with a specific substring (`=' or `:' by
        default).

        Values can span multiple lines, as long as they are indented deeper
        than the first line of the value. Depending on the parser's mode, blank
        lines may be treated as parts of multiline values or ignored.

        Configuration files may include comments, prefixed by specific
        characters (`#' and `;' by default). Comments may appear on their own
        in an otherwise empty line or may be entered in lines holding values or
        section names.
        """
        out_dict = {}
        elements_added = set()
        cursect = None  # None, or a dictionary
        sectname = None
        optname = None
        lineno = 0
        indent_level = 0
        e = None  # None, or an exception

        for lineno, line in enumerate(list_in, start=1):

            comment_start = sys.maxsize
            # strip comments

            for prefix in self._comment_prefixes:
                if line.strip().startswith(prefix):
                    comment_start = 0
                    break

            if comment_start == sys.maxsize:
                inline_pos = [comment_start]
                for prefix in self._inline_comment_prefixes:
                    index = line.find(prefix)
                    if index == -1:
                        continue
                    if index == 0 or (index > 0 and line[index - 1].isspace()):
                        inline_pos.append(index)
                comment_start = min(inline_pos)

            if comment_start == sys.maxsize:
                value = line.strip()
            elif comment_start == 0:
                value = None
            else:
                value = line[:comment_start].strip()

            if not value:
                # empty line marks end of value
                indent_level = sys.maxsize
                continue

            # continuation line?
            first_nonspace = self.NONSPACECRE.search(line)
            cur_indent_level = first_nonspace.start() if first_nonspace else 0

            if (cursect is not None and optname and
                        cur_indent_level > indent_level):

                cursect[optname].append(value)

            # a section header or option header?
            else:
                indent_level = cur_indent_level
                # is it a section header?

                mo = self.SECTCRE.match(value)

                if mo:
                    sectname = mo.group('header')

                    if sectname in out_dict:
                        if self._strict:
                            raise DuplicateSectionError(sectname, filename, lineno)
                        cursect = out_dict[sectname]

                    else:
                        cursect = {}
                        out_dict[sectname] = cursect
                        elements_added.add(sectname)
                    # So sections can't start with a continuation line
                    optname = None

                # no section header in the file?
                elif cursect is None:
                    raise MissingSectionHeaderError(filename, lineno, line)

                # an option line?
                else:

                    mo = self._optcre.match(value)

                    if mo:
                        optname, vi, optval = mo.group('option', 'vi', 'value')

                        if not optname:
                            e = self._handle_error(e, filename, lineno, line)

                        optname = optname.strip()
                        if self._strict and optname in cursect:
                            raise DuplicateOptionError(sectname, optname,
                                                       filename, lineno)

                        # This check is fine because the OPTCRE cannot
                        # match if it would set optval to None
                        if optval is not None:
                            optval = optval.strip()
                            cursect[optname] = [optval]

                        else:
                            # valueless option handling
                            cursect[optname] = None
                    else:
                        # a non-fatal parsing error occurred. set up the
                        # exception but keep going. the exception will be
                        # raised at the end of the file and will contain a
                        # list of all bogus lines
                        e = self._handle_error(e, filename, lineno, line)
        # if any parsing errors occurred, raise an exception
        if e:
            raise e

        for key, item in out_dict.items():
            if self.manager._no_sections:
                if isinstance(item, list):
                    out_dict[key] = '\n'.join(item).rstrip()
            else:
                for option, value in item.items():
                    if isinstance(value, list):
                        out_dict[key][option] = '\n'.join(value).rstrip()

        return out_dict

    # ****************************************************************************************************
    # *** Write files section
    # ****************************************************************************************************

    def _dict_to_list(self, dict_in, new_line=True):

        tmp_list = []
        if self._flat_dict:
            tmp_list.extend(self._format_section(dict_in, 'DEFAULT', new_line=new_line))
        else:
            for k, s in dict_in.items():
                tmp_list.extend(self._format_section(s, k, new_line))

        return tmp_list

    def _format_section(self, option_dict, section_name, new_line):

        tmp_ret = []
        if new_line:
            line_end = '\n'
        else:
            line_end = ''

        if self._space_around_delimiters:
            delimiter = " {} ".format(self._delimiters[0])
        else:
            delimiter = self._delimiters[0]

        tmp_ret.append("[{}]{}".format(section_name, line_end))
        for key, value in option_dict.items():
            if value is not None:
                value = delimiter + str(value).replace('\n', '\n\t')
            else:
                value = ""
            tmp_ret.append("{}{}{}".format(key, value, line_end))
        if new_line:
            tmp_ret.append(line_end)
        return tmp_ret

    def write(self, section_name=None, storage_name=storage_name, **kwargs):
        """
        will write to an INI file.
        """
        self.data = None
        tmp_dict_to_save = self._get_dict(section_name=section_name, storage_name=storage_name)
        self.data = self._dict_to_list(tmp_dict_to_save, False)

        return self.last_section_count, self.last_option_count


    def _handle_error(self, exc, fpname, lineno, line):
        if not exc:
            exc = ParsingError(fpname)
        exc.append(lineno, repr(line))
        return exc


class ConfigFileStorage(ConfigStringStorage):
    """
    A file manager that stores config files in a text file

    this manager can handle multiple files, as well as a string or list of data, as long as the data is in the format
    of an ini file.  it can also handle scanning a directory or list of directories for all files matching a filter
    pattern.

    if multiple files or filenames are passed, the files read will be processed in the order they are listed, with
    sections being merged and options overwriting older ones.

    if a directory path is passed, the files will be sorted based on the "read_path_order" option and processed in that
    order.

    :param tuple delimiters: the delimiter between the key and the value
    :param tuple comment_prefixes:  this is a tuple of characters that if they occur as the first non-whitespace
        character of a line, the line is a comment
    :param tuple inline_comment_prefixes: this is a tuple of characters that if they occur elsewhere in the line after a
        whitespace char, the rest of the line is a comment.
    :param bool space_around_delimiters: True if space should be added around the delimeters.
    :param bool strict: if False, duplicate sections will be merged, if True, duplicate sections will raise an error
    :param read_filenames: a filename or list of file names, assumed to be in the current directory if not otherwise
        specified for reading.  These can also be path/globs and the system will attempt to read all files matching
        that glob filter.  for example, the following are all exampels of valid parameters::

            'myfile.ini'
            'dir/myfile.ini'
            'dir/\*.ini'
            ['myfile.ini', 'myotherfile.ini', 'backup_files/myfile_??.ini']

        The filename to read from can also be passed during the read operation.
    :type read_filenames: str or list
    :param read_path_order: 'alpha' (default) or 'date', the order files will be processed if a path is passed.
    :param str filename: If used, the single file to read and write to. (cannot be used with read_filenames
        write_filename.)
    :param write_filename: the filename to write files to.
        if None and read_filenames is passed, this will take the first name in the list.
        if None and read_paths is passed, AND if there is ONLY ONE file in the path that matches the filter,
        this will use that file.
        the filename to write to can also be passed during the write operation.
    :type write_filename: str or None
    :param bool leave_open: if True, the file objects will be left open while the config manager is loaded.  this can
        speed up file access, but it also uses up file handles, buffers, memory, and has the possibility of
        corrupted files.
    :param bool create_files: if False, will not create any files it does not find.
    :param bool fail_if_no_file: if False, will fail and raise an error if the specified filename is not found.
    :param bool make_backup_before_writing: if True, the system will make a backup file before writing the configuration.
    :param str backup_filename: the filename of the backup file.  this can have the following formatting keys:
        '{NUM}' for an incremental number (uses the next available number)
        '{DATE}' for a date string ('YYYYMMDD')
        '{STIME}' for a 1 second resolution time string ('HHMMSS')
        '{MTIME}' for a 1 minute resolution time string {'HHMM')
        '{NAME}' for the old config file name (without extension)
    :param str backup_path: if not None (the default) this allows the backup file to be in a different location.
    :param int max_backup_number: the max number (assuming a backup file and NUM in the filename)
    :param str encoding:
    :return:
    """

    storage_type_name = 'INI File'
    storage_name = 'file'  #: the internal name of the storage manager, must be unique

    _create_files = True
    _fail_if_no_file = False
    _make_backup_before_writing = False
    _backup_filename = '{NAME}_{DATE}_{STIME}.bak'
    _backup_path = None
    _max_backup_number = 999
    _encoding = None

    # you should have EITHER a single filename
    _filename = None

    # OR file names and sets.
    _read_filenames = None
    _read_path_order = 'alpha'
    _read_path_order_dir = 'asc'
    _write_filename = None

    def config(self, config_dict):
        """
        :param dict config_dict: a dictionary with storage specific configuration options., This is called after the
            storage manager is loaded.
        """
        super(ConfigFileStorage, self).config(config_dict=config_dict)

        self._create_files = config_dict.get('create_files', self._create_files)
        self._fail_if_no_file = config_dict.get('fail_if_no_file', self._fail_if_no_file)
        self._make_backup_before_writing = config_dict.get('make_backup_before_writing',
                                                           self._make_backup_before_writing)
        self._backup_filename = config_dict.get('backup_filename', self._backup_filename)
        self._backup_path = config_dict.get('backup_path', self._backup_path)
        self._max_backup_number = config_dict.get('max_backup_number', self._max_backup_number)
        self._encoding = config_dict.get('encoding', self._encoding)

        self._read_path_order = config_dict.get('read_path_order', self._read_path_order)
        self._read_path_order_dir = config_dict.get('read_path_order_dir', self._read_path_order_dir)

        self._filename = config_dict.get('filename', self._filename)

        if self._filename is None:
            self._read_filenames = config_dict.get('read_filenames', self._read_filenames)
            self._write_filename = config_dict.get('write_filename', self._write_filename)
        else:
            self._read_filenames = [self._filename]
            self._write_filename = self._filename

    @property
    def get_default_filename(self):
        tmp_fn = Path(sys.argv[0])
        return tmp_fn.with_suffix('.ini')

    def read(self, section_name=None, storage_name=storage_name, files=None, encoding=None, **kwargs):
        """
        will read an ini file and save it to the system

        :param section_name:
        :type section_name: str or list
        :param str storage_name:
        :param file:
        :type file: str or FileObject
        :param str encoding:
        :return:
        :rtype: int
        """

        dicts_list = []

        if self.data is None:

            if self._fail_if_no_file:
                on_does_not_exist = 'raise'
            else:
                on_does_not_exist = 'ignore'

            if encoding is None:
                encoding = self._encoding

            if files is None:
                files = self._read_filenames

            if files is None:
                files = self.get_default_filename

            files = make_list(files)

            path_list = PathHandler(files, glob_sort_order=self._read_path_order,
                                    glob_sort_dir=self._read_path_order_dir,
                                    return_type='handle',
                                    verify='call',
                                    on_does_not_exist=on_does_not_exist,
                                    default_open_encoding=encoding)

            for file in path_list.readable:
                with file:
                    dicts_list.append(self._parse_list(file, file.name))

        else:
            if isinstance(self.data, str):
                self.data = self.data.splitlines()

            dicts_list.append(self._parse_list(self.data, 'passed_file'))

        out_dict = merge_dictionaries(dicts_list)

        self._save_dict(out_dict, section_name, storage_name)
        self.data = None

        return self.last_section_count, self.last_option_count

    def _make_backup(self, filename):
        """
        creates a formatted backup filename.
        """
        dt_date = datetime.now().strftime('%Y%m%d')
        dt_stime = datetime.now().strftime('%H%M%S')
        dt_mtime = datetime.now().strftime('%H%M')

        dest_fn = None
        name = Path(filename).name
        format_dict = dict(name=name, date=dt_date, stime=dt_stime, mtime=dt_mtime, num='*')

        backup_filename = copy.copy(self._backup_filename)
        backup_filename = backup_filename.format(format_dict)

        # if the path needs a number, test for it.
        if '*' in backup_filename:
            num_key = '{:0' + str(len(str(self._max_backup_number))) + '}'
            backup_filename = backup_filename.replace('*', num_key)

            for n in range(self._max_backup_number):
                tmp_filename = backup_filename.format(num=n)
                test_path = Path(self._backup_path, tmp_filename)
                if not test_path.exists():
                    dest_fn = str(test_path)
                    break
        else:
            dest_fn = backup_filename

        if dest_fn is not None:
            shutil.copy(filename, dest_fn)
        else:
            ip.warning('Destination filename could not be created')

    def write(self, section_name=None, storage_name=storage_name, file=None, encoding=None, **kwargs):
        """
        will write to an INI file.
        """

        self.data = None
        tmp_dict_to_save = self._get_dict(section_name=section_name, storage_name=storage_name)
        self.data = self._dict_to_list(tmp_dict_to_save)

        exists = True
        if file is None:
            if self._write_filename is None:
                filename = self.get_default_filename
                exists = filename.exists()
            else:
                filename = Path(self._write_filename)

        elif isinstance(file, str):
            filename = Path(file)
            exists = filename.exists()

            if not exists and not self._create_files:
                raise FileNotFoundError()

        if exists and self._make_backup_before_writing:
            # noinspection PyUnboundLocalVariable
            self._make_backup(filename.name)

        if file is None:
            file = filename.open(mode='w', encoding=encoding)

        for l in self.data:
            file.write(l)

        file.close()

        return self.last_section_count, self.last_option_count

    def _handle_error(self, exc, fpname, lineno, line):
        if not exc:
            exc = ParsingError(fpname)
        exc.append(lineno, repr(line))
        return exc


class StorageManagerManager(object):
    """
    A class to handle storage managers
    """

    def __init__(self, config_manager,
                 managers=None,
                 cli_parser_name='cli',
                 cli_manager=None,
                 storage_config=None,
                 default_storage_managers=None):
        """
        :param config_manager: a link to the ConfigurationManager object
        :param managers: the managers to be registered.  The first manager passed will be imported as the default
        :param cli_parser_name: the name of the cli parser if not 'cli', if None, this will disable CLI parsing.
        :param cli_manager: None uses the standard CLI Parser, this allows replacement of the default cli manager
        """
        self.config_manager = config_manager
        self.storage_managers = {}
        self.manager_list = []

        if default_storage_managers is None:
            self.default_managers = []
        else:
            self.default_managers = default_storage_managers

        self._storage_config = {}

        if storage_config is not None:
            self._storage_config = storage_config

        if managers is not None:
            if not isinstance(managers, (list, tuple)):
                managers = [managers]

            for a in managers:
                self.register_storage(a)

        if cli_parser_name is not None:
            if cli_parser_name not in self:
                if cli_manager is None:
                    cli_manager = ConfigCLIStorage
                cli_manager.storage_name = cli_parser_name
                self.register_storage(cli_manager)

    def register_storage(self, storage_manager):
        ip.debug('registering storage manager')

        storage_manager = storage_manager()
        storage_manager.manager = self.config_manager
        tmp_storage_config = self._storage_config.get(storage_manager.storage_name, dict())
        storage_manager.config(tmp_storage_config)

        self.storage_managers[storage_manager.storage_name] = storage_manager

        # storage_manager.config(self._storage_config[storage_manager.storage_name])

        if self.default_managers is not None and storage_manager.storage_name in self.default_managers:
            ip.a().debug('is listed as a default manager').s()
            self.manager_list.append(storage_manager)
        elif not self.default_managers and storage_manager.standard:
            ip.a().debug('is a standard manager (and no listings present').s()
            self.manager_list.append(storage_manager)
        else:
            ip.a().debug('is not going to be a default manager')
            ip.a().debug('default managers: ', self.default_managers)
            ip.debug('standard state:', storage_manager.standard).s(2)

        self._sort_list()

        ip.info('Storage Manager [', storage_manager.storage_name, '] registered')

    def _sort_list(self):
        self.manager_list.sort(key=lambda x: x.priority)

    def get(self, tag=None):
        if tag is None:
            ip.debug('fetching default storage:')

            return self.default_manager

        try:
            tmp_ret = self.storage_managers[tag]
            ip.debug('fetching storage for: ', tmp_ret)
            return tmp_ret

        except KeyError:
            ip.debug('storage not found for: ', tag)

            raise NoStorageManagerError(tag)

    def get_data(self, tag=None):
        return self.get(tag).data

    def set_data(self, data, tag=None):
        self.get(tag).data = data

    def read(self, sections=None, storage_names=None, override_tags=False, data=None):
        """
        runs the read from storage process for the selected or configured managers

        :param storage_names: If None, will read from all starnard storage managers, if a string or list, will read from
            the selected ones following the configured tag settings.
        :param sections: If None, will read from all sections, if string or list, will read from the selected ones
            following the configured tag settings.
        :param override_tags: if True, this will override the configured storage name settings allowing things like
            exporting the full config etc.
        :param data: if a single storage name is passed, then data can be passed to that storage manager for saving.
            this will raise an AssignmentError if data is not None and more than one storage name is passed.
        """

        tmp_section_count = 0
        tmp_option_count = 0
        tmp_storage_manager_count = 0

        tmp_run_list = []

        if storage_names is None:
            tmp_run_list.extend(self.manager_list)
        else:
            storage_names = make_list(storage_names)

            for t in storage_names:
                tmp_run_list.append(self.get(t))

        if data is not None and tmp_run_list:
            if len(tmp_run_list) == 1:
                tmp_run_list[0].data = data
            else:
                raise AttributeError('Data cannot be passed when reading from multiple storage managers')

        for s in tmp_run_list:
            tmp_storage_manager_count += 1
            if override_tags:
                use_tag = '*'
            else:
                use_tag = s.storage_name

            tsc, toc = s.read(sections, use_tag)
            tmp_section_count += tsc
            tmp_option_count += toc

        ip.info('read from storage managers').a()
        ip.info('sections: ', tmp_section_count)
        ip.info('options: ', tmp_option_count)
        ip.info('managers: ', tmp_storage_manager_count).s()

    def write(self, sections=None, storage_names=None, override_tags=False, **kwargs):
        """
        runs the write to storage process for the selected or configured managers

        :param storage_names: If None, will write to all starnard storage managers, if a string or list, will write to
            the selected ones following the configured tag settings.
        :param sections: If None, will write to all sections, if string or list, will write to the selected ones
            following the configured tag settings.
        :param override_tags: if True, this will override the configured storage name settings allowing things like
            exporting the full config etc.
        :return: if ONLY one storage_name is passed, this will return the data from that manager if present.
        """

        ip.info('writing data to storage locations').a()

        tmp_run_list = []

        tmp_section_count = 0
        tmp_option_count = 0
        tmp_storage_manager_count = 0

        if storage_names is None:
            tmp_run_list.extend(self.manager_list)
            ip.debug('using all registered standard managers')
        else:
            storage_names = make_list(storage_names)
            ip.debug('making a list...').a()
            ip.debug('registered storages: ', self.storage_managers)
            for t in storage_names:
                ip.debug('adding: ', self.storage_managers[t].storage_name)

                tmp_d = self.get(t)
                ip.debug('test:', tmp_d, ' tag ', t)
                tmp_run_list.append(self[t])

        ip.s().debug('Storages to write to: ', tmp_run_list)
        for s in tmp_run_list:
            tmp_storage_manager_count += 1
            if override_tags:
                use_tag = '*'
            else:
                use_tag = s.storage_name

            ip.debug('writing to : ', s).a()
            tsc, toc = s.write(sections, use_tag, **kwargs)
            ip.s()
            tmp_section_count += tsc
            tmp_option_count += toc

        ip.info('sections: ', tmp_section_count)
        ip.info('options: ', tmp_option_count)
        ip.info('managers: ', tmp_storage_manager_count).s()

        if len(tmp_run_list) == 1:
            return tmp_run_list[0].data
        else:
            return None

    def __call__(self):
        return self.default_manager

    def __getitem__(self, item):
        return self.get(item)

    def __iter__(self):
        for s in self.manager_list:
            yield s

