__author__ = 'dstrohl'
__all__ = ['DataTypeList', 'DataTypeStr', 'DataTypeFloat', 'DataTypeInt', 'DataTypeDict',
           'DataTypeGenerator', 'data_type_generator', '_UNSET']


import ast
import copy
from AdvConfigMgr.utils import make_list, convert_to_boolean
from AdvConfigMgr.config_validation import ValidationError


class UnSet(object):
    UnSetValidationString = '_*_This is the Unset Object_*_'
    """
    Used in parser getters to indicate the default behaviour when a specific
    option is not found it to raise an exception. Created to enable `None' as
    a valid fallback value.
    """
    def __repr__(self):
        return 'Empty Value'

    def __str__(self):
        return 'Empty Value'

    def __get__(self):
        return str(self)

    def __eq__(self, other):
        return isinstance(other, UnSet)


_UNSET = UnSet()


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
        tmp_ret = self._type_class(ast.literal_eval(value))
        return tmp_ret

    def to_string(self, value):
        """
        Returns a string version of the value passed.
        """
        return self._convert_to_string(value)

    def from_string(self, value, validate=True):
        """
        Returns an object matching the datatype from a string
        """
        return self._convert_from_string(value)

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


data_type_generator = DataTypeGenerator(DataTypeFloat, DataTypeList, DataTypeStr,
                                        DataTypeInt, DataTypeDict, DataTypeBoolean)
