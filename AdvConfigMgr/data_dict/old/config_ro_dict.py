__author__ = 'dstrohl'

__all__ = ['ConfigDict']

from AdvConfigMgr.data_dict.config_transform import Xform
from AdvConfigMgr.exceptions.config_exceptions import NoOptionError, NoSectionError
from AdvConfigMgr.utils.unset import _UNSET


class ConfigOptionRec(object):

    def __init__(self, section, name, value=_UNSET, default_value=_UNSET):
        self._section = section
        section, name = self._section._xf(name)
        self._name = name
        self._value = value
        self._default_value = default_value

    @property
    def is_empty(self):
        return self._default_value == _UNSET and self._value == _UNSET

    @property
    def path(self):
        return self._section.name + '.' + self.name

    @property
    def has_set_value(self):
        return self._value != _UNSET

    @property
    def has_default_value(self):
        return self._default_value != _UNSET

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
            return self._default_value
        return _UNSET


class ConfigSectionDict(object):

    def __init__(self, base_dict, name, options=None):
        """
        :type base_dict: ConfigDict
        """
        self._base_dict = base_dict
        self.name = name
        self._options_dict = {}

        if options is not None:
            self.add(options)

    def _add(self, option, value=_UNSET):
        section, option = self._xf(option)
        if self._xf_this_sec(section):
            self._options_dict[option] = ConfigOptionRec(self, option, default_value=value)
            return self._options_dict[option]

    def add(self, options, value=None):
        tmp_ret = {}
        if isinstance(options, dict):
            for option, d_value in options.items():
                tmp_ret[option] = self._add(option, d_value)
        else:
            tmp_ret = self._add(options, value)

        return tmp_ret

    def _xf(self, option):
        return self._base_dict._xform.both(option, section=self.name)

    def _xf_this_sec(self, section):
        return section is _UNSET or section == self.name or section is None
    '''
    def _parsable(self, option):
        return self._base_dict._xform.is_dot_notation(option)
    '''
    def get(self, option, raw=False):
        section, option = self._xf(option)
        if raw:
            return self.item(option).value
        else:
            return self._interpolate(self.item(option).value)

    def _interpolatable(self, option=None, value=None):
        if self._base_dict._interpolator is None:
            return False
        else:
            if option is not None:
                value = self[self._xf(option)]
            return self._base_dict._interpolator.interpolatorable(value)

    def _interpolate(self, value):
        if self._base_dict._interpolator is None or not isinstance(value, str):
            return value
        else:
            return self._base_dict._interpolator.before_get(self.name, value)

    def item(self, option):
        section, option = self._xf(option)
        if self._xf_this_sec(section):
            try:
                return self._options_dict[option]
            except KeyError:
                if self._base_dict._raise_on_does_not_exist:
                    raise NoOptionError(option=option, section=self.name)
        else:
            return self._base_dict[section][option]

    def __call__(self, option, value):
        return self.add(option, value)

    def __getitem__(self, option):
        return self.get(option)

    def __iter__(self):
        for key, item in self._options_dict.items():
            yield item

    def __contains__(self, option):
        section, option = self._xf(option)
        if self._xf_this_sec(section):
            return option in self._options_dict
        else:
            return option in self._base_dict[section]

    def __len__(self):
        return len(self._options_dict)

    def __str__(self):
        return self.name

    def __repr__(self):
        msg = '{} Options Dict, {} options'.format(self.name, len(self))
        return msg


class ConfigDict(object):

    def __init__(self, import_dict=None):
        self._section_dict = {}
        self._interpolator = None

        self._xform = Xform()
        self._sec_opt_sep = '.'
        self._raise_on_does_not_exist = False

        if import_dict is not None:
            self._editable = True
            self.add(import_dict)
            self._editable = False

    def _xf(self, section):
        return self._xform.section(section)

    def _add(self, section, options=None):
        section = self._xf(section)
        self._section_dict[section] = ConfigSectionDict(self, section, options)
        return self._section_dict[section]

    def add(self, sections, options=None):
        tmp_ret = {}
        if isinstance(sections, (list, tuple)):
            if options is not None:
                raise AttributeError('options can only be added by this method when only ONE section is passed')
            for section in sections:
                tmp_ret[section] = self._add(section)

        elif isinstance(sections, dict):
            for section, d_options in sections.items():
                tmp_ret[section] = self._add(section, d_options)

        else:
            tmp_ret = self._add(sections, options)

        return tmp_ret

    def __call__(self, section):
        return self.add(section)

    def __getitem__(self, section):
        section = self._xf(section)
        option = self._xform.option()
        try:
            if option is _UNSET:
                return self._section_dict[section]
            else:
                return self._section_dict[section][option]
        except KeyError:
            if self._raise_on_does_not_exist:
                raise NoSectionError(section=section)

    def __contains__(self, section):
        section = self._xf(section)
        option = self._xform.option()
        if option is _UNSET:
            return section in self._section_dict
        else:
            try:
                return option in self._section_dict[section]
            except KeyError:
                if self._raise_on_does_not_exist:
                    raise NoSectionError(section=section)

    def __iter__(self):
        for key, item in self._section_dict.items():
            yield item

    def __len__(self):
        return len(self._section_dict)

    def __repr__(self):
        msg = 'Read Only Config Dict, {} sections'.format(len(self))
        return msg
