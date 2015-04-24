__author__ = 'dstrohl'

from .utils import Error, get_between, get_after
from .config_transform import Xform
from .config_exceptions import NoSectionError, NoOptionError
__all__ = ['Interpolation', 'NoInterpolation']


# ************************************************************************************
# *********  Errors
# ************************************************************************************


class InterpolationError(Error):
    """Base class for interpolation-related exceptions."""

    def __init__(self, msg):
        Error.__init__(self, msg)
        self.args = (msg, )


class InterpolationSyntaxError(InterpolationError):
    """Raised when the source text contains invalid syntax.

    Current implementation raises this exception when the source text into
    which substitutions are made does not conform to the required syntax.
    """


class InterpolationDepthError(InterpolationError):
    """Raised when substitutions are nested too deeply."""

    def __init__(self, instr, max_depth, rawval):
        msg = ("Value interpolation too deeply recursive:\n"
               "\tString In: {}\n"
               "\tMax Depth : {}\n"
               "\trawval : {}\n".format(instr, max_depth, rawval))
        InterpolationError.__init__(self, msg)
        self.args = (instr, max_depth, rawval)

# ************************************************************************************
# *********  Interpolation Classes
# ************************************************************************************


class BaseInterpolation:
    """Dummy interpolation that passes the value through with no changes."""

    raise_on_lookup_error = True
    replace_on_lookup_error = ''
    lookup_errors = (NoSectionError, NoOptionError)

    allow_cross_section_interpolation = True

    def __init__(self, base_config, xform, max_depth=10, enc='()', sep='.', key='%'):

        self.max_depth = max_depth
        self.enc = enc
        self.sep = sep
        self.key = key

        self.xform = xform

        self.key_start = enc[0]
        self.key_end = enc[1]

        self.base_config = base_config

    def interpolatorable(self, value):
        return False

    def before_get(self, section_name, value):
        """
        run on value returned from the config_root before returning it to the calling system.

        .. note:: this is the main interpolation location.

        :param section_name: the name of the current section
        :param value: the value from the config root
        :return: the value to be returned
        """
        return value

    def before_set(self, section_name, value):
        """
        run on values before saving them to the config_root from the calling system

        .. note:: Normally used to validate any interpolation keys

        :param section_name: the name of the current section
        :param value: the value to be saved
        :return: the interpolated value to be saved to the config_root
        """
        return value

    def before_read(self, section_name, value):
        """
        run on values after they are returned from storage and before they are saved to the config_root

        .. note:  Normally not used.

        :param section_name: the name of the current section
        :param value: the value from storage
        :return: the value to save to the config_root
        """
        return value

    def before_write(self, section_name, value):
        """
        run on values after they are returned from config_root and before they are saved to storage

        .. note: Normally not used.

        :param section_name: the name of the current section
        :param value: the value from the config_root
        :return: the value to save to the config_root
        """
        return value


class NoInterpolation(BaseInterpolation):
    pass


class Interpolation(BaseInterpolation):
    """Interpolation as implemented in the classic ConfigParser.

    The option values can contain format strings which refer to other values in
    the same section, or values in the special default section.

    For example:

        something: %(dir)s/whatever

    would resolve the "%(dir)s" to the value of dir.  All reference
    expansions are done late, on demand. If a user needs to use a bare % in
    a configuration file, she can escape it by writing %%. Other % usage
    is considered a user error and raises `InterpolationSyntaxError'.

    can also handle taking section option

    """

    def before_get(self, section_name, value):
        return self.interpolate(value, section_name)

    def before_set(self, section_name, value):
        return self.validate_interpolation_str(value)

    def interpolatorable(self, value):
        key_str = self.key+self.enc[0]
        if isinstance(value, str) and key_str in value:
            return True
        else:
            return False

    def validate_interpolation_str(self, in_string):
        """
        validates that the string passed does not have major structural errors.  This does not validate that any
        interpolation keys exist in any given field_map.

        :param in_string: the string to check
        :return: in_string if passed.  raises InterpolationSyntaxError if not.
        """
        if not isinstance(in_string, str):
            return in_string

        if self.key not in in_string:
            return in_string

        rest = in_string
        accum = []

        while rest:
            key_pos = rest.find(self.key)
            if key_pos < 0:
                return

            if key_pos >= 0:
                accum.append(rest[:key_pos])
                rest = rest[key_pos:]

            c = rest[1:2]
            if c == self.key:
                accum.append(self.key)
                rest = rest[2:]

            elif c == self.key_start:

                if self.key_end not in rest:
                    raise InterpolationSyntaxError("bad interpolation variable reference %r" % rest)

                rest = get_after(rest, self.key_end)

            else:
                raise InterpolationSyntaxError(
                    "'{0}' must be followed by '{0}' or '{2}', found: {1}".format(self.key, rest, self.key_start))

        return in_string

    '''
    def interpolate(self, 
                    in_string,
                    field_map,
                    depth=0,
                    max_depth=10,
                    key='%',
                    key_sep='.',
                    key_enc='()',
                    current_path='',
                    on_key_error='raise',
                    error_replace='',
                    errors_to_except=None):
    '''

    '''
    max_depth = 10
    enc = '()'
    sep = '.'
    key = '%'
    xform = Xform(sec_opt_sep=sep)

    raise_on_lookup_error = True
    replace_on_lookup_error = ''
    lookup_errors = (NoSectionError, NoOptionError)

    key_start = enc[0]
    key_end = enc[1]
    '''

    def interpolate(self, in_string, section, depth=0):
        """
        Interpolator Engine:

        This will interpolate key strings from a passed string by looking them up in a dictionary.  The dictionary can
        be multi leveled and strings can be passed as a path string (i.e. '.path1.path2.path3.dict_key')

        .. note:: If a non string is passed, it is returned with no changes.

        :param in_string: the initial string to parse, if this is not a string, we will return it as it is with no
            processing.
        :param section: the string name of the section being processed.
        :return:  the final interpolated string.
        """
        # int_field_map = MultiLevelDictManager(field_map, current_path, key_sep)

        int_field_map = self.base_config
        
        if not isinstance(in_string, str):
            return in_string

        if self.key not in in_string:
            return in_string

        rest = in_string
        accum = []

        if depth > self.max_depth:
            raise InterpolationDepthError(in_string, self.max_depth, rest)

        while rest:
            key_pos = rest.find(self.key)
            if key_pos < 0:
                return

            if key_pos >= 0:
                accum.append(rest[:key_pos])
                rest = rest[key_pos:]

            c = rest[1:2]

            if c == self.key:
                accum.append(self.key)
                rest = rest[2:]

            elif c == self.key_start:

                if self.key_end not in rest:
                    raise InterpolationSyntaxError("bad interpolation variable reference %r" % rest)

                dot_n, matched = self.xform.full_check(get_between(rest, self.key_start, self.key_end), section=section)
                if dot_n:
                    new_section = self.xform.section()
                else:
                    new_section = section

                if self.raise_on_lookup_error:
                    key_value = int_field_map[matched]
                else:
                    try:
                        key_value = int_field_map[matched]
                    except self.lookup_errors:
                        key_value = self.replace_on_lookup_error

                if self.key in key_value:
                    depth += 1
                    if depth > self.max_depth:
                        raise InterpolationDepthError(in_string, self.max_depth, rest)

                    key_value = self.interpolate(key_value, section=new_section, depth=depth)

                accum.append(key_value)

                rest = get_after(rest, self.key_end)

            else:
                raise InterpolationSyntaxError(
                    "'{0}' must be followed by '{0}' or '{2}', found: {1}".format(self.key, rest, self.key_start))

        return ''.join(accum)
