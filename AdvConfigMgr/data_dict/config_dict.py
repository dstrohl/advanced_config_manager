from AdvConfigMgr.utils.base_utils import Path, _UNSET, pluralize
from collections import OrderedDict
import re
from .config_transform import xform, interpolate
from copy import deepcopy, copy

class ConfigDictOption(object):
    _is_section = False
    _is_option = True

    def __init__(self, name, section, value=_UNSET, as_default=False):
        self._name = name
        self._section = section
        self._value = _UNSET
        self._default = _UNSET
        self.set(value, as_default=as_default)

    @property
    def name(self):
        return self._name

    def get(self, **kwargs):
        raw = kwargs.get('raw', False)
        if self._value is _UNSET:
            if 'default' in kwargs:
                tmp_ret = kwargs['default']
            else:
                tmp_ret = self._default
        else:
            tmp_ret = self._value

        if raw:
            return tmp_ret
        else:
            return interpolate(tmp_ret, self._section)

    def set(self, value, as_default=False):
        if isinstance(value, ConfigDictOption):
            self._value = value._value
            self._default = value._default
        else:
            if as_default:
                self._default = value
            else:
                self._value = value

    def clear(self, **kwargs):
        tmp_ret = self.get()
        self._value = _UNSET
        return tmp_ret

    @property
    def has_value(self):
        return self._value is not _UNSET or self._default is not _UNSET

class ConfigDict(object):
    _is_section = True
    _is_option = False

    _parent = None
    _root = None
    _is_root = True
    _name = None
    _locked = False
    _path = '.'

    def __init__(self,
                 *data_in,
                 name=None,
                 parent=None,
                 section_depth=0,
                 section_regex=None,
                 load_as_default=True,
                 lock_after_load=False,
                 key_sep='.',
                 **kwargs):
        """
        :param dict_db: the dictionary to use for lookups.  The keys for this must be strings.
        :param current_path: the current path string (see :py:class:`Path` for more info on path strings)
        :param key_sep: the string to use to separate the keys in the path, by default '.'
        """
        self._root = self

        self._name = name or 'Root'

        self._sections = kwargs.get('sections_dict', OrderedDict())
        self._options = kwargs.get('options_dict', OrderedDict())

        self._set_parent(parent)

        self._key_sep = key_sep
        if section_regex is None:
            self._section_regex = None
        else:
            self._section_regex = re.compile(section_regex)
        self._section_depth = section_depth

        self._update(*data_in, as_default=load_as_default)

        if lock_after_load:
            self._lock()
        # self._path = Path(current_path, key_sep=key_sep)
        # self.key_sep = key_sep

    def _set_parent(self, parent=None, name=None):
        self._parent = parent
        if name is not None:
            self._name = name

        if parent is None:
            self._root = self
            self._is_root = True
        else:
            self._is_root = False
            self._root = self._parent._root
            if self._parent._path == '.':
                self._path = self._parent._path+self._name
            else:
                self._path = self._parent._path+'.'+self._name

        for sec_name, section in self._sections.items():
            section._set_parent(parent=self)

    def _parse_path(self, path, maxhop=0, hop=0, return_best=False, create_section=False):

        if path[:3] == ''.ljust(3, self._key_sep):
            try:
                return self._parent._parse_path(path[1:], maxhop=maxhop, hop=hop+1)
            except AttributeError:
                raise AttributeError('Invalid path: %s, no parent path defined' % path)

        elif path[:2] == ''.ljust(2, self._key_sep):
            try:
                return self._parent._parse_path(path[2:], maxhop=maxhop, hop=hop+1)
            except AttributeError:
                raise AttributeError('Invalid path: %s, no parent path defined' % path)

        elif path[:1] == self._key_sep:
            try:
                return self._root._parse_path(path[1:], maxhop=maxhop, hop=hop+1)
            except AttributeError:
                raise AttributeError('Invalid path: %s, no root path defined' % path)
        else:
            if self._key_sep in path:
                next_hop, new_path = path.split(self._key_sep, maxsplit=1)
                if next_hop in self._sections:
                    return self._sections[next_hop]._parse_path(new_path, maxhop=maxhop, hop=hop+1)
                elif create_section:
                    self._local_add_section(next_hop)
                    return self._sections[next_hop]._parse_path(new_path, maxhop=maxhop, hop=hop+1)
                elif return_best:
                    return self, path
                else:
                    raise AttributeError('Invalid path: %s' % path)
            else:
                return self, path

    def _lock(self, recurse=False):
        if recurse:
            for sec in self._sections.values():
                sec._lock(recurse=recurse)
        self._locked = True

    def _unlock(self, recurse=False):
        if recurse:
            for sec in self._sections.values():
                sec._unlock(recurse=recurse)
        self._locked = False

    def _local_add_section(self, name, data=None, **kwargs):

            if not isinstance(data, ConfigDict):
                if not isinstance(data, dict) and data is not None:
                    raise TypeError('Only dictionaries or ConfigDict objects can be sections')

                tmp_sec_depth = kwargs.get('section_depth', self._section_depth)

                if 'section_regex_compiled' in kwargs:
                    tmp_sec_regex = kwargs['section_regex_compiled']
                elif 'section_regex' in kwargs and kwargs['section_regex'] is not None:
                    tmp_sec_regex = re.compile(kwargs['section_regex'])
                else:
                    tmp_sec_regex = self._section_regex

                if tmp_sec_depth > 0:
                    tmp_sec_depth = self._section_depth - 1

                data = ConfigDict(data, parent=self, name=name, key_sep=self._key_sep,
                                  section_depth=tmp_sec_depth, section_regex=tmp_sec_regex)

            else:
                data._set_parent(parent=self, name=name)

            self._sections[name] = data

            if name in self._options:
                del self._options[name]

    def _set(self, key, value, **kwargs):
        obj, path = self._parse_path(key, create_section=kwargs.get('create_section', False))
        obj._local_set(path, value, **kwargs)

    def _lock_check(self):
        if self._locked:
            raise PermissionError('%s is locked' % self._name)

    def _local_set(self, key, value, as_section=False, as_default=False, **kwargs):
        self._lock_check()

        tmp_sec_depth = kwargs.get('section_depth', self._section_depth)
        tmp_sec_regex = kwargs.get('section_regex')
        if tmp_sec_regex is not None:
            tmp_sec_regex = re.compile(tmp_sec_regex)
        else:
            tmp_sec_regex = self._section_regex

        if not as_section:
            if isinstance(value, ConfigDict):
                as_section = True
            else:
                if tmp_sec_regex is not None:
                    if tmp_sec_regex.match(key):
                        as_section = True

                else:
                    if tmp_sec_depth > 0:
                        as_section = True

        if as_section:
            obj, path = self._parse_path(key, create_section=True)
            obj._local_add_section(name=path, data=value, key_sep=self._key_sep,
                                   section_depth=tmp_sec_depth, section_regex=tmp_sec_regex)
        else:
            if key in self._options:
                self._options[key].set(value, as_default=as_default)
            else:
                if not isinstance(value, ConfigDictOption):
                    value = ConfigDictOption(name=key, section=self, value=value, as_default=as_default)
                self._options[key] = value
                if key in self._sections:
                    del self._sections[key]

    def _update(self, *data_in, create_section=False, **kwargs):
        self._lock_check()

        for data in data_in:
            if isinstance(data, ConfigDict):
                if data._name is None:
                    raise AttributeError('Name must be defined when passing ConfigDict objects')
                self._local_set(data._name, data, as_section=True)
            elif isinstance(data, dict):
                for key, item in data.items():
                    self._set(key, item, **kwargs)
            elif data is None:
                return
            else:
                raise TypeError('%r is not a dict' % data)

    def _interpolate(self, value):
        if not isinstance(value, str):
            return value
        ret_str = interpolate(value, self)

        return ret_str

    def _get(self, key, default=None, raw=False):
        obj, path = self._parse_path(key)
        if path == '':
            return obj
        return obj._local_get(path, default=default, raw=raw)

    def _local_get(self, key, default=None, raw=False):
        try:
            return self._local_getitem(key, raw=raw)
        except KeyError:
            if raw:
                return default
            else:
                return self._interpolate(default)

    def _getitem(self, key, raw=False):
        try:
            obj, path = self._parse_path(key)
        except AttributeError as err:
            raise KeyError(str(err))
        if path == '':
            return obj
        return obj._local_getitem(path, raw=raw)

    def _local_getitem(self, key, raw=False):
        try:
            return self._options[key].get(raw=raw)
        except KeyError:
            return self._sections[key]

    def _delitem(self, key):
        obj, path = self._parse_path(key)
        if path == '':
            raise('invalid delete item path: %s' % key)
        obj._local_delitem(path)

    def _local_delitem(self, key):
        self._lock_check()
        try:
            del self._options[key]
        except KeyError:
            del self._sections[key]

    def _contains(self, key):
        obj, path = self._parse_path(key)
        if path == '':
            raise('invalid delete item path: %s' % key)
        return obj._local_contains(path)

    def _local_contains(self, key):
        if key in self._sections:
            return True
        if key in self._options and self._options[key].has_value:
            return True
        return False

    def _clear(self, path=None, recurse=False):

        if path is None:
            obj = self
            path = ''
        else:
            obj, path = self._parse_path(path)

        if path == '':
            obj._local_clear(recurse=recurse)
        else:
            obj._local_clear(path, recurse=recurse)

    def _local_clear(self, option=None, recurse=False):
        self._lock_check()

        if option is None:
            for opt in self._options.values():
                opt.clear()
            if recurse:
                for sec in self._sections.values():
                    sec._clear(recurse=recurse)
        else:
            if option in self._options:
                self._options[option].clear()
            elif option in self._sections:
                self._sections[option].clear(recurse=recurse)

    def _keys(self, sections_only=False, options_only=False):
        tmp_keys = []
        if not options_only:
            for s in self._sections:
                tmp_keys.append(s)
        if not sections_only:
            for o in self._options:
                tmp_keys.append(o)
        return tmp_keys

    __getitem__ = _getitem
    __setitem__ = _set
    __call__ = _get
    __delitem__ = _delitem
    __contains__ = _contains

    def __str__(self):
        return self._name

    def __repr__(self):
        sec_count = len(self._sections)
        opt_count = len(self._options)

        return 'ConfigDict(%s) [%s %s, %s %s]' % (
            self._path,
            sec_count,
            pluralize(sec_count, 'section'),
            opt_count,
            pluralize(opt_count, 'option'))

    def __getattr__(self, item):
        try:
            return self._sections[item]
        except KeyError:
            raise AttributeError('%s is not a valid section' % item)

    def __len__(self):
        return len(self._options) + len(self._sections)

    def __delattr__(self, item):
        self._lock_check()

        if item in self._sections:
            del self._sections[item]
        else:
            super(ConfigDict, self).__delattr__(item)

    def __eq__(self, other):
        return self._name == other._name and \
            self._sections == other._sections and \
            self._options == other._options

    def __iter__(self):
        for s in self._sections.values():
            yield s
        for o in self._options.values():
            yield o

    def __copy__(self):
        """
        copy(ConfigDict) will return a copy of the existing dict as if it was the root, any changes to this dict
        will be mirrored in the original dict.
        :return:
        """
        return type(self)(
             section_depth=self._section_depth,
             section_regex=self._section_regex,
             lock_after_load=self._locked,
             key_sep=self._key_sep,
             sections_dict=self._sections,
             options_dict=self._options)

    def __deepcopy__(self, memo):
        """
        deepcopy(ConfigDict) will return a NEW version of the existing dict as if it was the root, with
        new copies of all sections and options.
        :param memo:
        :return:
        """
        not_there = []
        existing = memo.get(self, not_there)
        if existing is not not_there:
            return existing

        dup = type(self)(
             name=self._name,
             parent=self._parent,
             section_depth=self._section_depth,
             section_regex=self._section_regex,
             lock_after_load=self._locked,
             key_sep=self._key_sep)

        memo[self] = dup

        dup._sections = deepcopy(self._sections, memo)
        dup._options = deepcopy(self._options, memo)

        return dup

    def __hash__(self):
        return hash(self.__repr__())
