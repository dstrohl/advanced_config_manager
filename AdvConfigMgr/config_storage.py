__author__ = 'dstrohl'

from CompIntel.Core.Config.config_exceptions import *
from PythonUtils import make_list
from argparse import ArgumentParser
import copy

__all__ = ['BaseConfigStorageManager','StorageManagerManager','ConfigCLIStorage','ConfigSimpleDictStorage']


class BaseConfigStorageManager(object):
    """
    defines an expandable storage subsystem for configs
    """
    storage_type_name = 'Base'
    storage_tag = None          #: the internal name of the storage manager, must be unique
    force_strings = False       #: True if the storage only accepts strings
    standard = True             #: True if this should be used for read_all/write_all ops
    allow_create = False        #: True if this can create options in the system, even if they are not pre-configured
    force = False               #: True if this will set options even if they are locked
    overwrite = False           #: True if this will overwrite options that have existing values
    lock_after_read = False     #: True if this will lock the option after reading
    last_section_count = 0
    last_option_count = 0

    manager = None

    data = None


    def __init__(self,
                 storage_tag=None,
                 allow_create=None,
                 standard=None,
                 force=None,
                 overwrite=None,
                 lock_after_read=None,
                 priority=100):
        """

        :param storage_tag:
        :param allow_create:
        :param standard:
        :param force:
        :param overwrite:
        :param lock_after_read:
        :param priority:
        :return:
        """
        self.storage_tag = storage_tag or self.storage_tag
        self.allow_create = allow_create or self.allow_create
        self.force = force or self.force
        self.standard = standard or self.standard
        self.overwrite = overwrite or self.overwrite
        self.lock_after_read = lock_after_read or self.lock_after_read
        self.priority = priority

        ip.info('Loading storage manager: ', self.storage_tag)

    def read(self, *args,  **kwargs):
        """
        read from storage and save to the system
        :param args:
        :param force: will add option even if locked
        :param overwrite: will overwrite existing value if present, otherwise this will skip
        :param kwargs:
        :return: the number of sections / options added
        """
        raise NotImplementedError
        return self.last_section_count, self.last_option_count

    def write(self, *args, **kwargs):
        """
        Write to storage from the system
        :param args:
        :param kwargs:
        :return: the number of sections / option written
        """
        raise NotImplementedError
        return self.last_section_count, self.last_option_count

    @property
    def _am_i_default(self):
        return self.manager.storage.default_manager is self

    def _ok_to_read_section(self, section_name, storage_tag=storage_tag):
        if section_name not in self.manager:
            if self.allow_create and self.manager.allow_create_from_storage:
                self.manager.add_section(dict(name=section_name, storage_write_to=self.storage_tag))
                return True
            else:
                return False
        if storage_tag == '*':
            return True

        tmp_section_tag = self.manager[section_name].storage_read_from

        if tmp_section_tag is None:
            return True
        if storage_tag in list(tmp_section_tag):
            return True
        return False

    def _ok_to_write_section(self, section_name, storage_tag=storage_tag):

        if storage_tag == '*':
            return True

        tmp_section_tag = self.manager[section_name].storage_write_to
        if tmp_section_tag is None:
            if self._am_i_default:
                return True
            else:
                return False
        if tmp_section_tag == '*' or tmp_section_tag == storage_tag:
            return True
        return False

    def _get_dict(self, section_name=None, storage_tag=storage_tag):
        """
        returns a dictionary of options.

        :param section_name: a string name of a section or list of section names to get to.  if this is a single
            string, it is assumed it is the base of the dictionary and all keys are options, if this is None or if it
            is a tuple/list, it is assumed that the keys of the dictionary are sections, containing dictionaries of
            options.
            If this is None, all sections will be queried based on their storage tag.  this does NOT override the
            storage_tag.
        :param storage_tag: allows overriding the storage tag
        :return:
        """
        ip.debug('storage [', self.storage_tag, '] creating a dictionary of options.').push()
        self.last_section_count = 0
        self.last_option_count = 0

        tmp_ret = {}

        if isinstance(section_name, str) or self.manager._no_sections:
            flat_dict = True
        else:
            flat_dict = False

        section_name = make_list(section_name)

        ip.debug('section name parameter: ', section_name)

        for section in self.manager:
            ip.debug('storage [', self.storage_tag, '] checking section ', section.name)

            ok_2_get = False
            if section_name == [None] or section.name in section_name:
                ip.debug('storage [', self.storage_tag, '] section selectable', section.name)

                if self._ok_to_write_section(section.name, storage_tag):
                    ip.debug('storage [', self.storage_tag, '] checking allowed ', section.name)
                    if len(section) > 0:
                        ip.debug('storage [', self.storage_tag, '] checking has content ', section.name)
                        ok_2_get = True

            if ok_2_get:
                ip.debug('storage [', self.storage_tag, '] getting section ', section.name)

                tmp_sec = {}

                self.last_section_count += 1
                for option in section:
                    opt_success, opt_value = self._get_option(section, option)
                    if opt_success:
                        self.last_option_count += 1
                        tmp_sec[option.name] = opt_value

                if flat_dict:
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
        ip.debug('getting option [', option, '] for storage ', self.storage_tag).a()

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

    def _save_dict(self, dict_in, section_name=None, storage_tag=storage_tag):
        """
        takes a dictionary and saves it to the system

        :param dict_in: the dictionary to save.
            if a single section name is passed, OR if the config manager is set to simple config (no sections), this
            should be a dictionary of options.  otherwise this should be a dictionary of sections, each a dictionary
            of options.
        :param section_name: a string name of a section or list of section names to save to.  if this is a single
            string, it is assumed it is the base of the dictionary and all keys are options, if this is None or if it
            is a tuple/list, it is assumed that the keys of the dictionary are sections, containing dictionaries of
            options
            This does not override the storage tags.
        :param storage_tag: allows overriding the storage tag
        """
        self.last_section_count = 0
        self.last_option_count = 0

        if self.manager.no_sections:
            section_name = self.manager._DEFAULT_SECT_NAME

        if isinstance(section_name, str):
            dict_in = {section_name: dict_in}

        for section, options in dict_in.items():
            if self._ok_to_read_section(section, storage_tag):
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
        ip.debug('reading option [', option_name, '] from storage ', self.storage_tag).a()
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
        return self.storage_type_name+' ['+self.storage_tag+']'

class ConfigCLIStorage(BaseConfigStorageManager):
    """
    Read configuration from the CLI
    """
    storage_type_name = 'CLI Manager'
    storage_tag = 'cli'
    standard = True             #: True if this should be used for read_all/write_all ops
    force_strings = False       #: True if the storage only accepts strings
    force = True               #: True if this will set options even if they are locked
    overwrite = True           #: True if this will overwrite options that have existing values
    lock_after_read = True     #: True if this will lock the option after reading
    priority = 1

    _reset_config_cache = True

    _cli_parser = None

    data = None

    def read(self, section_name=None, storage_tag=storage_tag):
        """
        will take a dictionary and save it to the system
        :param dict_in:
        :param storage_tag:
        :return:
        """

        self._parse_cli(self.data)
        self.data = None

        return self.last_section_count, self.last_option_count


    def write(self, section_name=None, storage_tag=storage_tag):
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
    storage_tag = 'dict'
    standard = False             #: True if this should be used for read_all/write_all ops

    def read(self, section_name=None, storage_tag=storage_tag):
        """
        will take a dictionary and save it to the system
        :param dict_in:
        :param storage_tag:
        :return:
        """
        self._save_dict(self.data, section_name, storage_tag)
        return self.last_section_count, self.last_option_count

    def write(self, section_name=None, storage_tag=storage_tag):
        """
        will return a dictionary from the system
        :param storage_tag:
        :return:
        """
        self.data = self._get_dict(section_name, storage_tag)
        return self.last_section_count, self.last_option_count


class StorageManagerManager(object):
    """
    A class to handle storage managers
    """
    default_cli_manager = ConfigCLIStorage()

    def __init__(self, config_manager, *managers, cli_parser_name='cli', cli_manager=default_cli_manager):
        """
        :param config_manager: a link to the ConfigurationManager object
        :param managers: the managers to be registered.  The first manager passed will be imported as the default
        :param skip_cli: if True will not load the default cli manager
        :param cli_manager: allows replacement of the default cli manager
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

        if cli_parser_name is not None and 'cli' not in self:
            cli_manager.storage_tag = cli_parser_name
            self.register_storage(cli_manager)

    def register_storage(self, storage_manager, default=True):
        ip.debug('registering storage manager')

        storage_manager.manager = self.config_manager
        self.tag_dict[storage_manager.storage_tag] = storage_manager

        if default or self.default_manager is None:
            self.default_manager = storage_manager

        if storage_manager.standard:
            self.manager_list.append(storage_manager)

        self._sort_list()

        ip.info('Storage Manager [', storage_manager.storage_tag, '] registered')



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

    def read(self, sections=None, storage_tags=None, override_tags=False, data=None):
        """
        runs the read from storage process for the selected or configured managers

        :param storage_tags: If None, will read from all starnard storage managers, if a string or list, will read from
            the selected ones following the configured tag settings.
        :param sections: If None, will read from all sections, if string or list, will read from the selected ones
            following the configured tag settings.
        :param override_tags: if True, this will override the configured storage tag settings allowing things like
            exporting the full config etc.
        :param data: if a single storage tag is passed, then data can be passed to that storage manager for saving.
            this will raise an AssignmentError if data is not None and more than one storage tag is passed.
        """

        tmp_section_count = 0
        tmp_option_count = 0
        tmp_storage_manager_count = 0

        tmp_run_list = []

        if storage_tags is None:
            tmp_run_list.extend(self.manager_list)
        else:
            storage_tags = make_list(storage_tags)

            for t in storage_tags:
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
                use_tag = s.storage_tag

            tsc, toc = s.read(sections, use_tag)
            tmp_section_count += tsc
            tmp_option_count += toc

        ip.info('read from storage managers').a()
        ip.info('sections: ', tmp_section_count)
        ip.info('options: ', tmp_option_count)
        ip.info('managers: ', tmp_storage_manager_count).s()

    def write(self, sections=None, storage_tags=None, override_tags=False):
        """
        runs the write to storage process for the selected or configured managers

        :param storage_tags: If None, will write to all starnard storage managers, if a string or list, will write to the
            selected ones following the configured tag settings.
        :param sections: If None, will write to all sections, if string or list, will write to the selected ones
            following the configured tag settings.
        :param override_tags: if True, this will override the configured storage tag settings allowing things like
            exporting the full config etc.
        :return: if ONLY one storage_tag is passed, this will return the data from that manager if present.
        """

        tmp_run_list = []

        tmp_section_count = 0
        tmp_option_count = 0
        tmp_storage_manager_count = 0

        if storage_tags is None:
            tmp_run_list.extend(self.manager_list)
        else:
            storage_tags = make_list(storage_tags)
            ip.debug('making a list...').a()
            ip.debug('registered storages: ', self.tag_dict)
            for t in storage_tags:

                ip.debug('adding: ', self.tag_dict[t].storage_tag)

                tmp_d = self.get(t)
                ip.debug('test:', tmp_d, ' tag ', t)
                tmp_run_list.append(self[t])

        ip.s().debug('Storages to write to: ', tmp_run_list)
        for s in tmp_run_list:
            tmp_storage_manager_count += 1
            if override_tags:
                use_tag = '*'
            else:
                use_tag = s.storage_tag

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



'''
class ConfigFileStorage(BaseConfigStorageManager):


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



    def __init__(self,
                 delimiters=('=', ':'),
                 comment_prefixes=('#', ';'),
                 inline_comment_prefixes=None ):
        self._delimiters = tuple(delimiters)
        if delimiters == ('=', ':'):
            self._optcre = self.OPTCRE_NV if allow_no_value else self.OPTCRE
        else:
            d = "|".join(re.escape(d) for d in delimiters)
            if allow_no_value:
                self._optcre = re.compile(self._OPT_NV_TMPL.format(delim=d),
                                          re.VERBOSE)
            else:
                self._optcre = re.compile(self._OPT_TMPL.format(delim=d),
                                          re.VERBOSE)
        self._comment_prefixes = tuple(comment_prefixes or ())
        self._inline_comment_prefixes = tuple(inline_comment_prefixes or ())




class ConfigStringStorage(BaseConfigStorageManager):
    pass
'''

'''
    def read(self, filenames, encoding=None):
        """Read and parse a filename or a list of filenames.

        Files that cannot be opened are silently ignored; this is
        designed so that you can specify a list of potential
        configuration file locations (e.g. current directory, user's
        home directory, systemwide directory), and all existing
        configuration files in the list will be read.  A single
        filename may also be given.

        Return list of successfully read files.
        """
        if isinstance(filenames, str):
            filenames = [filenames]
        read_ok = []
        for filename in filenames:
            try:
                with open(filename, encoding=encoding) as fp:
                    self._read(fp, filename)
            except OSError:
                continue
            read_ok.append(filename)
        return read_ok

    def read_file(self, f, source=None):
        """Like read() but the argument must be a file-like object.

        The `f' argument must be iterable, returning one line at a time.
        Optional second argument is the `source' specifying the name of the
        file being read. If not given, it is taken from f.name. If `f' has no
        `name' attribute, `<???>' is used.
        """
        if source is None:
            try:
                source = f.name
            except AttributeError:
                source = '<???>'
        self._read(f, source)

    def read_string(self, string, source='<string>'):
        """Read configuration from a given string."""
        sfile = io.StringIO(string)
        self.read_file(sfile, source)


    def readfp(self, fp, filename=None):
        """Deprecated, use read_file instead."""
        warnings.warn(
            "This method will be removed in future versions.  "
            "Use 'parser.read_file()' instead.",
            DeprecationWarning, stacklevel=2
        )
        self.read_file(fp, source=filename)


    def write(self, fp, space_around_delimiters=True):
        """Write an .ini-format representation of the configuration state.

        If `space_around_delimiters' is True (the default), delimiters
        between keys and values are surrounded by spaces.
        """
        if space_around_delimiters:
            d = " {} ".format(self._delimiters[0])
        else:
            d = self._delimiters[0]
        if self._defaults:
            self._write_section(fp, self.default_section,
                                self._defaults.items(), d)
        for section in self._sections:
            self._write_section(fp, section,
                                self._sections[section].items(), d)

    def _write_section(self, fp, section_name, section_items, delimiter):
        """Write a single section to the specified `fp'."""
        fp.write("[{}]\n".format(section_name))
        for key, value in section_items:
            value = self._interpolation.before_write(self, section_name, key,
                                                     value)
            if value is not None or not self._allow_no_value:
                value = delimiter + str(value).replace('\n', '\n\t')
            else:
                value = ""
            fp.write("{}{}\n".format(key, value))
        fp.write("\n")


    def _read(self, fp, fpname):
        """Parse a sectioned configuration file.

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
        elements_added = set()
        cursect = None  # None, or a dictionary
        sectname = None
        optname = None
        lineno = 0
        indent_level = 0
        e = None  # None, or an exception
        for lineno, line in enumerate(fp, start=1):
            comment_start = sys.maxsize
            # strip inline comments
            inline_prefixes = {p: -1 for p in self._inline_comment_prefixes}
            while comment_start == sys.maxsize and inline_prefixes:
                next_prefixes = {}
                for prefix, index in inline_prefixes.items():
                    index = line.find(prefix, index + 1)
                    if index == -1:
                        continue
                    next_prefixes[prefix] = index
                    if index == 0 or (index > 0 and line[index - 1].isspace()):
                        comment_start = min(comment_start, index)
                inline_prefixes = next_prefixes
            # strip full line comments
            for prefix in self._comment_prefixes:
                if line.strip().startswith(prefix):
                    comment_start = 0
                    break
            if comment_start == sys.maxsize:
                comment_start = None
            value = line[:comment_start].strip()
            if not value:
                if self._empty_lines_in_values:
                    # add empty line to the value, but only if there was no
                    # comment on the line
                    if (comment_start is None and
                                cursect is not None and
                            optname and
                                cursect[optname] is not None):
                        cursect[optname].append('')  # newlines added at join
                else:
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
                    if sectname in self._sections:
                        if self._strict and sectname in elements_added:
                            raise DuplicateSectionError(sectname, fpname,
                                                        lineno)
                        cursect = self._sections[sectname]
                        elements_added.add(sectname)
                    elif sectname == self.default_section:
                        cursect = self._defaults
                    else:
                        cursect = self._dict()
                        self._sections[sectname] = cursect
                        self._proxies[sectname] = SectionProxy(self, sectname)
                        elements_added.add(sectname)
                    # So sections can't start with a continuation line
                    optname = None
                # no section header in the file?
                elif cursect is None:
                    raise MissingSectionHeaderError(fpname, lineno, line)
                # an option line?
                else:
                    mo = self._optcre.match(value)
                    if mo:
                        optname, vi, optval = mo.group('option', 'vi', 'value')
                        if not optname:
                            e = self._handle_error(e, fpname, lineno, line)
                        optname = self.optionxform(optname.rstrip())
                        if (self._strict and
                                    (sectname, optname) in elements_added):
                            raise DuplicateOptionError(sectname, optname,
                                                       fpname, lineno)
                        elements_added.add((sectname, optname))
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
                        e = self._handle_error(e, fpname, lineno, line)
        # if any parsing errors occurred, raise an exception
        if e:
            raise e
        self._join_multiline_values()

    def _join_multiline_values(self):
        defaults = self.default_section, self._defaults
        all_sections = itertools.chain((defaults,),
                                       self._sections.items())
        for section, options in all_sections:
            for name, val in options.items():
                if isinstance(val, list):
                    val = '\n'.join(val).rstrip()
                options[name] = self._interpolation.before_read(self,
                                                                section,
                                                                name, val)

    def _handle_error(self, exc, fpname, lineno, line):
        if not exc:
            exc = ParsingError(fpname)
        exc.append(lineno, repr(line))
        return exc


'''

