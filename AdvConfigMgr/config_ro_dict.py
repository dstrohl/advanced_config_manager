__author__ = 'dstrohl'

__all__ = ['ConfigDict']


from AdvConfigMgr.config_exceptions import NoOptionError, NoSectionError, LockedSectionError
from AdvConfigMgr.utils.unset import _UNSET
from AdvConfigMgr.config_transform import Xform

class ConfigSectionDict(object):

    def __init__(self, base_dict, name, options=None):
        """
        :type base_dict: ConfigDict
        """

        self._base_dict = base_dict
        self.name = name
        self._options_dict = {}

        if options is not None:
            tmp_base_dict = self._base_dict._editable
            self._base_dict._editable = True
            self.add(options)
            self._base_dict._editable = tmp_base_dict

    def _add(self, option, value):
        if self._base_dict.editable:
            option = self._xf(option)
            self._options_dict[option] = value
            return self._options_dict[option]

    def add(self, options, value=None):
        tmp_ret = {}
        if self._base_dict.editable:
            if isinstance(options, dict):
                for option, d_value in options.items():
                    tmp_ret[option] = self._add(option, d_value)
            else:
                tmp_ret = self._add(options, value)
        return tmp_ret

    def _xf(self, option):
        return self._base_dict._xform.option(option)

    def _parsable(self, option):
        return self._base_dict._xform.is_dot_notation(option)

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

    def __call__(self, option, value):
        return self.add(option, value)

    def __getitem__(self, item):
        if self._parsable(item):
            return self._base_dict[item]
        else:
            item = self._xf(item)
            try:
                tmp_ret = self._options_dict[item]
                return self._interpolate(tmp_ret)
            except KeyError:
                if self._base_dict._raise_on_does_not_exist:
                    raise NoOptionError(option=item, section=self.name)

    def __setitem__(self, option, value):
        if self._base_dict.editable and self._parsable(option):
            self._base_dict[option] = value
        else:
            self._options_dict[self._xf(option)] = value

    def __iter__(self):
        for key, item in self._options_dict.items():
            yield item

    def __contains__(self, option):
        if self._parsable(option):
            return option in self._base_dict
        else:
            return self._xf(option) in self._options_dict

    def __delitem__(self, option):
        if self._base_dict.editable and self._parsable(option):
            del self._base_dict[option]
        else:
            option = self._xf(option)
            if option in self:
                del self._options_dict[option]
            else:
                if self._base_dict._raise_on_does_not_exist:
                    raise NoOptionError(option=option, section=self.name)

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
        self._editable = False
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
        if self.editable:
            section = self._xf(section)
            self._section_dict[section] = ConfigSectionDict(self, section, options)
            return self._section_dict[section]

    def add(self, sections, options=None):
        tmp_ret = {}
        if self.editable:
            if isinstance(sections, (list, tuple)):
                if options is not None:
                    raise AttributeError('options can only be added when ONE section is passed')
                for section in sections:
                    tmp_ret[section] = self._add(section)
            if isinstance(sections, dict):
                for section, d_options in sections.items():
                    tmp_ret[section] = self._add(section, d_options)
            else:
                tmp_ret = self._add(sections, options)
        return tmp_ret


    @property
    def editable(self):
        if not self._editable:
            raise LockedSectionError('Editing must be done from within ConfigManager')
        return True

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

    def __setitem__(self, section, value):
        if self.editable:
            section = self._xf(section)
            option = self._xform.option()
            if option is _UNSET:
                if value is _UNSET:
                    self.add(section)
                else:
                    raise AttributeError('Sections must be added using ".add"')
            else:
                if section in self:
                    self._section_dict[section][option] = value
                else:
                    if self._raise_on_does_not_exist:
                        raise NoSectionError(section=section)

    def __delitem__(self, section):
        if self.editable:
            section = self._xf(section)
            option = self._xform.option()
            try:
                if option is _UNSET:
                    del self._section_dict[section]
                else:
                    tmp_section = self._section_dict[section]
                    del tmp_section[option]
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
