__author__ = 'dstrohl'
__all__ = ['DataTypeList', 'DataTypeStr', 'DataTypeFloat', 'DataTypeInt', 'DataTypeDict', 'DataTypeBoolean',
           'DataTypeLooseVersion', 'DataTypeStrictVersion',
           'DataTypeGenerator', 'data_type_generator']

import ast
import copy
from .utils import make_list, convert_to_boolean, slugify, get_after, get_before
from .config_validation import ValidationError
# from .config_exceptions import log
from unicodedata import normalize
from .utils.unset import _UNSET
from distutils.version import LooseVersion, StrictVersion
from .config_logging import get_log

log = get_log(__name__)


'''
class ItemKey(object):
    _sec_opt_sep = '.'
    _def_glob_chars = '*?[]!'
    _def_no_glob_chars = '_'

    def __init__(self, name=None, **kwargs):

        self._section = None
        self._sect_compare = None
        self._option = None
        self._dot = False
        self._xform_class = Xform()
        
        glob = kwargs.pop('glob', None)
        if glob:
            self._glob_chars = self._def_glob_chars
        else:
            self._glob_chars = self._def_no_glob_chars

        self._save_and_xform(name=name, **kwargs)

    def _set_sec(self, section):
        self._section = self._xform_class.section(section, self._glob_chars)

    def _set_opt(self, option):
        self._option = self._xform_class.option(option, self._glob_chars)
        self._sect_compare = self._xform_class.section(option, self._glob_chars)

    def _save_dot_not(self, name):
        if self._sec_opt_sep is not None and self._sec_opt_sep in name:a
            self._set_sec(get_before(name, self._sec_opt_sep))
            self._set_opt(get_after(name, self._sec_opt_sep))
            self._dot = True
            return None
        if self._sec_opt_sep is None and self._sec_opt_sep in name:
            msg = 'Dot Notation disabled : {}'.format(name)
            raise AttributeError(msg)
        return name

    def _save_and_xform(self, name=None, **kwargs):

        name = kwargs.get('name', name)
        if name is not None:
            if type(name) == type(self):
                self._section = name.section
                self._option = name.option
                self._sect_compare = name._sect_compare

            elif isinstance(name, str):
                if self._save_dot_not(name) is not None:
                    self._set_sec(name)
                    self._set_opt(name)

        if 'section' in kwargs:
            section = kwargs['section']

            if isinstance(section, str):
                if self._save_dot_not(section) is not None:
                    self._set_sec(section)
            elif type(section) == type(self):
                self._section = name.section
            else:
                self._section = section

        if 'option' in kwargs:
            option = kwargs['option']

            if isinstance(option, str):
                if self._save_dot_not(option) is not None:
                    self._set_opt(option)
            elif type(option) == type(self):
                self._option = name.option
            else:
                self._option = option

        return self

    @property
    def section(self):
        return self._section

    @property
    def option(self):
        return self._option

    @property
    def s(self):
        return self._section

    @property
    def o(self):
        return self._option

    @property
    def has_both(self):
        return self._section == self._sect_compare

    def __str__(self):
        if self._section == self._sect_compare:
            return self.s
        else:
            return '{}{}{}'.format(self.s, self._sec_opt_sep, self.o)

    def __call__(self, name=None, **kwargs):
        return self._save_and_xform(name, **kwargs)

    def __eq__(self, other):
        if isinstance(other, str):
            return str(self) == other
        elif type(other) == type(self):
            return str(self) == str(other)

    def __repr__(self):
        return str(self)
'''


class DataTypeGenerator(object):
    def __init__(self, *args):
        self._type_classes = {}
        for t in args:
            self.register_type(t)

    def register_type(self, dt):
        if not issubclass(dt, DataTypeBase):
            raise TypeError('Data Type class is not a sub-class of DataTypeBase')
        self._type_classes[dt.name] = dt

    def get(self, dt):
        if dt in self._type_classes:
            return self._type_classes[dt]
        else:
            msg = 'Datatype {} not recognized for: {}'.format(type(dt).__name__, dt)
            raise TypeError(msg)

    def __call__(self, dt):
        return self.get(dt)


class DataTypeBase(object):
    name = 'str'
    _type_class = str

    def __init__(self, validations=None, allow_empty=True, empty_type=_UNSET):
        """
        :param allow_empty: set to False if validation should be raised on empty or blank fields.
        :param empty_types: set to a tuple of types that are considered empty
        :param validations: a list or tuple of validation classes to run.
        """
        if validations is not None:
            self.validations = make_list(validations)
        else:
            self.validations = None
        self.empty_type = empty_type
        self.allow_empty = allow_empty

    def __call__(self, value):
        return self.validated(value)

    def add_validations(self, validations):
        self.validations = make_list(validations)

    def auto_convert(self, value):
        if isinstance(value, self._type_class):
            return value
        else:
            return self._type_class(value)

    def validated(self, value):
        """
        Runs all validations and returns the value if validated.
        :param value: value to be validated
        :return:
        """

        if self.allow_empty:
            if value == self.empty_type:
                return value

        if self._validate_datatype(value):
            return self._validations(value)
        else:
            tmp_msg = '%r is does not match the datatype requirement of %s' % (value, self.name)
            raise ValidationError(tmp_msg)

            # return self._validations(value) and self._validate_datatype(value)

    def _validations(self, value):
        if self.validations is not None:
            for v in self.validations:
                v.validate(value)
        return value

    def _validate_datatype(self, value):
        """
        Returns a True/False depending on if the object matches the datatype defined.
        Can be overwritten to validate the datatype.
        """
        return isinstance(value, self._type_class)

    @staticmethod
    def _convert_to_string(value):
        """
        Should return a string version of the value passed
        Shoudl be over-ridden for types that "str" does not work for.
        """
        tmp_str = str(value)
        return tmp_str

    def _convert_from_string(self, value):
        """
        Should returns an object matching the datatype from a string
        Should be over-ridden for non-string types
        """
        return self._type_class(ast.literal_eval(value))


    def to_string(self, value):
        """
        Returns a string version of the value passed.
        """
        return self._convert_to_string(value)

    def from_string(self, value, validate=True):
        log.debug('convert from [%s]', value)
        if isinstance(value, str):
            return self._convert_from_string(value)
        else:
            if isinstance(value, self._type_class):
                return value
            else:
                msg = '{} is not a string or {}'.format(value, self.name)
                raise TypeError(msg)

    def __repr__(self):
        return 'Datatype Validator for: %s' % self.name


class DataTypeStr(DataTypeBase):
    name = 'str'

    @staticmethod
    def _convert_from_string(value):
        return value

    @staticmethod
    def _convert_to_string(value):
        return value


class DataTypeInt(DataTypeBase):
    name = 'int'
    _type_class = int


class DataTypeFloat(DataTypeBase):
    name = 'float'
    _type_class = float


class DataTypeList(DataTypeBase):
    name = 'list'
    _type_class = list


class DataTypeDict(DataTypeBase):
    name = 'dict'
    _type_class = dict


class DataTypeBoolean(DataTypeBase):
    name = 'bool'
    _type_class = bool

    def auto_convert(self, value):
        if isinstance(value, self._type_class):
            return value
        else:
            return convert_to_boolean(value)

    @staticmethod
    def _convert_to_string(value):
        if value:
            return "YES"
        else:
            return "NO"

    def _convert_from_string(self, value):
        return convert_to_boolean(value)


class DataTypeLooseVersion(DataTypeBase):
    name = 'LooseVersion'
    _type_class = LooseVersion

class DataTypeStrictVersion(DataTypeBase):
    name = 'StrictVersion'
    _type_class = StrictVersion


data_type_generator = DataTypeGenerator(DataTypeFloat, DataTypeList, DataTypeStr,
                                        DataTypeInt, DataTypeDict, DataTypeBoolean)
