__author__ = 'dstrohl'

from AdvConfigMgr.config_exceptions import *
from AdvConfigMgr.config_types import _UNSET
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
           'ConfigFileStorage']


class BaseConfigStorageManager(object):
    """

    Base class for storage managers, efines an expandable storage subsystem for configs

    at a minimum, any sub classes should define the following initial values:

    storage_type_name:
        (str) This is the name of the manager class, it is used in log entries and potentially UI's.

    storage_name:
        (str) This is the default name of the manager, it is used when selecting which manager to use.

    force_strings:
        (bool) If True, the system will convert all options to strings before writing to the manager, and from strings
        when reading from it.

    Also, the two methods; BaseConfigStorageManager.read() and BaseConfigStorageManager.write() need to be overwritten
    to read and write the data in the format needed.

    if the manager is intended to be a 'standard' one, in other words, if it will be used for automatic
    read-all/write-all processes, it must be able to run without passing any data or arguments, all configuration
    must be done during initialization.  if it will only be used standalone or on-demand, you can allow any information
    to be passed.

    """
    storage_type_name = 'Base'
    storage_name = None
    force_strings = False
    standard = True
    allow_create = False
    force = False
    overwrite = False
    lock_after_read = False

    def __init__(self,
                 manager,
                 storage_name=None,
                 allow_create=None,
                 standard=None,
                 force=None,
                 overwrite=None,
                 lock_after_read=None,
                 priority=100):
        """
        :param ConfigManager manager: a link to the :py:class:`ConfigManager` object.
        :param str storage_name: The internal name of the storage manager, must be unique
        :param bool allow_create: True if this can create options in the system, even if they are not pre-configured.
        :param bool standard:  True if this should be used for read_all/write_all ops
        :param bool force:True if this will set options even if they are locked
        :param bool overwrite: True if this will overwrite options that have existing values
        :param bool lock_after_read: True if this will lock the option after reading
        :param int priority: the priority of this manager, with smallest being run earlier than larger.
        :return:
        """
        self.storage_name = storage_name or self.storage_name
        self.allow_create = allow_create or self.allow_create
        self.force = force or self.force
        self.standard = standard or self.standard
        self.overwrite = overwrite or self.overwrite
        self.lock_after_read = lock_after_read or self.lock_after_read
        self.priority = priority

        self._flat_dict = None

        self.last_section_count = 0
        self.last_option_count = 0

        self.manager = manager

        self.data = None

        ip.info('Loading storage manager: ', self.storage_name)

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
        to :py:meth:`BaseConfigStorageManager._save_dict`.  that method will take care of writing the data, converting it
        if needed, making sure that it is allowed to write, handling locked sections and options, etc...

        if the implementation tries to pass data directly to the file manager for importing, it will save the data in
        :py:meth:`BaseConfigStorageManager.data` where you can read it, so you should check this before processing.

        You shoudl keep track of the number of sections and options written/read and return these at the end::

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

        you shoudl keep track of the number of sections and options written/read and return these at the end::

        return self.last_section_count, self.last_option_count
        """
        raise NotImplementedError

    @property
    def _am_i_default(self):
        return self.manager.storage.default_manager is self

    def _ok_to_read_section(self, section_name, storage_name=storage_name):
        if section_name not in self.manager:
            if self.allow_create and self.manager.allow_create_from_storage:
                self.manager.add_section(dict(name=section_name, storage_write_to=self.storage_name))
                return True
            else:
                return False
        if storage_name == '*':
            return True

        tmp_section_tag = self.manager[section_name].storage_read_from

        if tmp_section_tag is None:
            return True
        if storage_name in list(tmp_section_tag):
            return True
        return False

    def _ok_to_write_section(self, section_name, storage_name=storage_name):

        if storage_name == '*':
            return True

        tmp_section_tag = self.manager[section_name].storage_write_to
        if tmp_section_tag is None:
            if self._am_i_default:
                return True
            else:
                return False
        if tmp_section_tag == '*' or tmp_section_tag == storage_name:
            return True
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

    def _save_dict(self, dict_in, section_name=None, storage_name=storage_name):
        """
        Takes a dictionary and saves it to the system

        :param dict dict_in: the dictionary to save.
            if a single section name is passed, OR if the config manager is set to simple config (no sections), this
            should be a dictionary of options.  otherwise this should be a dictionary of sections, each a dictionary
            of options.
        :param section_name: a string name of a section or list of section names to save to.  if this is a single
            string, it is assumed it is the base of the dictionary and all keys are options, if this is None or if it
            is a tuple/list, it is assumed that the keys of the dictionary are sections, containing dictionaries of
            options
            This does not override the storage names.
        :type section_name: str or list or None
        :param str storage_name: allows overriding the storage name
        """
        self.last_section_count = 0
        self.last_option_count = 0

        if self.manager.no_sections:
            section_name = self.manager._DEFAULT_SECT_NAME

        if isinstance(section_name, str):
            dict_in = {section_name: dict_in}

        for section, options in dict_in.items():
            if self._ok_to_read_section(section, storage_name):
                self.last_section_count += 1
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
        return self.storage_type_name+' ['+self.storage_name+']'


class ConfigCLIStorage(BaseConfigStorageManager):
    """
    Read configuration from the CLI
    """
    storage_type_name = 'CLI Manager'
    storage_name = 'cli'
    standard = True             #: True if this should be used for read_all/write_all ops
    force_strings = False       #: True if the storage only accepts strings
    force = True               #: True if this will set options even if they are locked
    overwrite = True           #: True if this will overwrite options that have existing values
    lock_after_read = True     #: True if this will lock the option after reading
    priority = 1

    def __init__(self, *args, **kwargs):
        self._reset_config_cache = True
        self._cli_parser = None
        super(ConfigCLIStorage, self).__init__(*args, **kwargs)

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
    standard = False             #: True if this should be used for read_all/write_all ops

    def __init__(self, *args, **kwargs):
        super(ConfigSimpleDictStorage, self).__init__(*args, **kwargs)


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


class StorageManagerManager(object):
    """
    A class to handle storage managers
    """

    def __init__(self, config_manager, *managers, cli_parser_name='cli', cli_manager=None):
        """
        :param config_manager: a link to the ConfigurationManager object
        :param managers: the managers to be registered.  The first manager passed will be imported as the default
        :param cli_parser_name: the name of the cli parser if not 'cli', if None, this will disable CLI parsing.
        :param cli_manager: None uses the standard CLI Parser, this allows replacement of the default cli manager
        """
        self.config_manager = config_manager
        self.tag_dict = {}
        self.manager_list = []
        self.default_manager = None
        set_as_default = True

        if managers:
            for a in managers:
                self.register_storage(a, default=set_as_default)
                set_as_default = False

        if cli_parser_name is not None:
            if cli_parser_name not in self:
                if cli_manager is None:
                    cli_manager = ConfigCLIStorage()
                cli_manager.storage_name = cli_parser_name
                self.register_storage(cli_manager)

    def register_storage(self, storage_manager, default=True):
        ip.debug('registering storage manager')

        storage_manager.manager = self.config_manager
        self.tag_dict[storage_manager.storage_name] = storage_manager

        if default or self.default_manager is None:
            self.default_manager = storage_manager

        if storage_manager.standard:
            self.manager_list.append(storage_manager)

        self._sort_list()

        ip.info('Storage Manager [', storage_manager.storage_name, '] registered')

    def _sort_list(self):
        self.manager_list.sort(key=lambda x: x.priority)

    def get(self, tag=None):
        if tag is None:
            ip.debug('fetching default storage:')

            return self.default_manager

        try:
            tmp_ret = self.tag_dict[tag]
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

    def write(self, sections=None, storage_names=None, override_tags=False):
        """
        runs the write to storage process for the selected or configured managers

        :param storage_names: If None, will write to all starnard storage managers, if a string or list, will write to the
            selected ones following the configured tag settings.
        :param sections: If None, will write to all sections, if string or list, will write to the selected ones
            following the configured tag settings.
        :param override_tags: if True, this will override the configured storage name settings allowing things like
            exporting the full config etc.
        :return: if ONLY one storage_name is passed, this will return the data from that manager if present.
        """

        tmp_run_list = []

        tmp_section_count = 0
        tmp_option_count = 0
        tmp_storage_manager_count = 0

        if storage_names is None:
            tmp_run_list.extend(self.manager_list)
        else:
            storage_names = make_list(storage_names)
            ip.debug('making a list...').a()
            ip.debug('registered storages: ', self.tag_dict)
            for t in storage_names:

                ip.debug('adding: ', self.tag_dict[t].storage_name)

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

            ip.debug('writing to to: ', s).a()
            tsc, toc = s.write(sections, use_tag)
            ip.s()
            tmp_section_count += tsc
            tmp_option_count += toc

        ip.info('write to storage managers').a()
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

    def __setitem__(self, key, value):
        self.register_storage(value)

    def __iter__(self):
        for s in self.manager_list:
            yield s


class ConfigStringStorage(BaseConfigStorageManager):
    """
    A file manager that returns or saves configuration in the format of a string of list. in a text file

    this manager handles strings formatted as a standard INI file, or lists of strings formatted that way.
    """

    storage_type_name = 'INI String'
    storage_name = 'string'          #: the internal name of the storage manager, must be unique
    force_strings = True       #: True if the storage only accepts strings

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

    def __init__(self, *,
                 delimiters=('=', ':'),
                 comment_prefixes=('#', ';'),
                 inline_comment_prefixes=None,
                 space_around_delimiters=True,
                 strict=True,
                 **kwargs):
        """
        :param tuple delimiters: the delimiter between the key and the value
        :param tuple comment_prefixes:  this is a tuple of characters that if they occur as the first non-whitespace
            character of a line, the line is a comment
        :param tuple inline_comment_prefixes: this is a tuple of characters that if they occur elsewhere in the line after a
            whitespace char, the rest of the line is a comment.
        :param bool space_around_delimiters: True if space should be added around the delimeters.
        :param bool strict: if False, duplicate sections will be merged, if True, duplicate sections will raise an error
        :param kwargs: any required kwargs from the base storage manager
        :return:
        """
        self._delimiters = tuple(delimiters)
        if delimiters == ('=', ':'):
            self._optcre = self.OPTCRE_NV
        else:
            d = "|".join(re.escape(d) for d in delimiters)
            self._optcre = re.compile(self._OPT_NV_TMPL.format(delim=d), re.VERBOSE)

        self._comment_prefixes = tuple(comment_prefixes or ())
        self._inline_comment_prefixes = tuple(inline_comment_prefixes or ())
        self._space_around_delimiters = space_around_delimiters
        self._strict = strict

        super(ConfigStringStorage, self).__init__(**kwargs)

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
                    if index == 0 or (index > 0 and line[index-1].isspace()):
                        inline_pos.append(index)
                comment_start = min(inline_pos)

            if comment_start == sys.maxsize:
                value = line
            elif comment_start == 0:
                value = None
            else:
                value = line[:comment_start].rstrip()

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

        return out_dict

    # ****************************************************************************************************
    # *** Write files section
    # ****************************************************************************************************

    def _format_dict(self, sections, storage_name):
        tmp_dict_to_save = self._get_dict(sections, storage_name)

        tmp_list = []
        if self._flat_dict:
            tmp_list.extend(self._format_section(tmp_dict_to_save, 'DEFAULT'))
        else:
            for k, s in tmp_dict_to_save.items():
                tmp_list.extend(self._format_section(s, k))

        return tmp_list

    def _format_section(self, option_dict, section_name):

        tmp_ret = []

        if self._space_around_delimiters:
            delimiter = " {} ".format(self._delimiters[0])
        else:
            delimiter = self._delimiters[0]

        tmp_ret.append("[{}]\n".format(section_name))
        for key, value in option_dict:
            if value is not None:
                value = delimiter + str(value).replace('\n', '\n\t')
            else:
                value = ""
            tmp_ret.append("{}{}\n".format(key, value))
        tmp_ret.append("\n")
        return tmp_ret

    def write(self, section_name=None, storage_name=storage_name, **kwargs):
        """
        will write to an INI file.
        """
        self.data = None
        self.data = self._format_dict(section_name=section_name, storage_name=storage_name)

        return self.last_section_count, self.last_option_count

    '''
    def _join_multiline_value(self, val):
        if isinstance(val, list):
            val = '\n'.join(val).rstrip()
        return val

    def _handle_error(self, exc, fpname, lineno, line):
        if not exc:
            exc = ParsingError(fpname)
        exc.append(lineno, repr(line))
        return exc
    '''


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
    """

    storage_type_name = 'INI File'
    storage_name = 'txt'          #: the internal name of the storage manager, must be unique

    def __init__(self, *,
                 delimiters=('=', ':'),
                 comment_prefixes=('#', ';'),
                 inline_comment_prefixes=None,
                 space_around_delimiters=True,
                 strict=True,
                 read_filenames=None,
                 read_path_order='alpha',
                 read_path_order_dir='asc',
                 write_filename=None,
                 # leave_open=False,
                 create_files=True,
                 fail_if_no_file=False,
                 make_backup_before_writing=False,
                 backup_filename='{NAME}_{DATE}_{STIME}.bak',
                 backup_path=None,
                 max_backup_number=999,
                 encoding=None,
                 **kwargs):
        """
        :param tuple delimiters: the delimiter between the key and the value
        :param tuple comment_prefixes:  this is a tuple of characters that if they occur as the first non-whitespace
            character of a line, the line is a comment
        :param tuple inline_comment_prefixes: this is a tuple of characters that if they occur elsewhere in the line after a
            whitespace char, the rest of the line is a comment.
        :param bool space_around_delimiters: True if space should be added around the delimeters.
        :param bool strict: if False, duplicate sections will be merged, if True, duplicate sections will raise an error
        :param read_filenames: a filename or list of file names, assumed to be in the current directory if not otherwise
            specified for reading.  These can also be path/globs and the system will attempt to read all files matching
            that glob filter.  for example, the following are all exampels of valid parameters:
            'myfile.ini'
            'dir/myfile.ini'
            'dir/*.ini'
            ['myfile.ini', 'myotherfile.ini', 'backup_files/myfile_??.ini']
            The filename to read from can also be passed during the read operation.
        :type read_filenames: str or list
        :type read_path_order: 'alpha' (default) or 'date', the order files will be processed if a path is passed.
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
        :param kwargs: any required kwargs from the base storage manager
        :return:
        """
        self._delimiters = tuple(delimiters)
        if delimiters == ('=', ':'):
            self._optcre = self.OPTCRE_NV
        else:
            d = "|".join(re.escape(d) for d in delimiters)
            self._optcre = re.compile(self._OPT_NV_TMPL.format(delim=d), re.VERBOSE)

        self._comment_prefixes = tuple(comment_prefixes or ())
        self._inline_comment_prefixes = tuple(inline_comment_prefixes or ())
        self._space_around_delimiters = space_around_delimiters
        self._strict = strict
        self._encoding = encoding

        # self._leave_open = leave_open
        self._create_files = create_files
        self._fail_if_no_file = fail_if_no_file

        # self._files = None
        self._read_filenames = make_list(read_filenames)
        self._read_path_order = read_path_order
        self._read_path_order_dir = read_path_order_dir
        self._write_filename = write_filename

        self._make_backup_before_writing = make_backup_before_writing
        self._backup_path = backup_path
        self._backup_filename = backup_filename
        self._max_backup_num = max_backup_number

        # self.filenames(filenames)

        super(ConfigFileStorage, self).__init__(**kwargs)

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
            num_key = '{:0'+str(len(str(self._max_backup_num)))+'}'
            backup_filename = backup_filename.replace('*', num_key)

            for n in range(self._max_backup_num):
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
        self.data = self._format_dict(section_name, storage_name)

        exists = True
        if file is None:
            if self._write_filename is None:
                raise AttributeError('either a file object or a filename must be specified')
            else:
                filename = Path(self._write_filename)

        elif isinstance(file, str):
            filename = Path(file)
            exists = filename.exists()

            if not exists and not self._create_files:
                raise FileNotFoundError()

        if exists and self._make_backup_before_writing:
            self._make_backup(filename.name)

        if file is None:
            file = filename.open(mode='w', encoding=encoding)


        for l in self.data:
            file.write(l)

        file.close()

        return self.last_section_count, self.last_option_count
    '''
    def _join_multiline_value(self, val):
        if isinstance(val, list):
            val = '\n'.join(val).rstrip()
        return val
    '''

    def _handle_error(self, exc, fpname, lineno, line):
        if not exc:
            exc = ParsingError(fpname)
        exc.append(lineno, repr(line))
        return exc
