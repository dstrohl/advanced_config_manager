__author__ = 'dstrohl'

__all__ = ['Xform', 'Interpolation', 'NoInterpolation', 'interpolate', 'xform', 'interpolate_key_check',
           'InterpolationDepthError', 'InterpolationSyntaxError']

from AdvConfigMgr.exceptions.config_exceptions import NoSectionError, NoOptionError
from AdvConfigMgr.utils import Error, get_between, get_after, get_before
from unicodedata import normalize
from AdvConfigMgr.utils.unset import _UNSET


class Xform(object):

    def __init__(self, sec_opt_sep='.', glob_chars='*?[]!_', glob_no_chars='_'):
        self._section_cache = {}
        self._section_glob_cache = {}
        self._option_cache = {}
        self._option_glob_cache = {}
        self._sec_opt_sep = sec_opt_sep
        self._def_glob_chars = glob_chars
        self._def_no_glob_chars = glob_no_chars
        self._last_option = _UNSET
        self._last_section = _UNSET
        self._last_dot_not = _UNSET

    def option_x_form(self, optionstr, glob=False):
        """
        Will transform the option name string as needed, by default this will slugify and lowercase the string.

        This also caches the return to minimize the times through the transformer.

        This can be overridden as desired.
        """
        if glob:
            try:
                return self._option_glob_cache[optionstr]
            except KeyError:
                tmp_ret = self.slugify(optionstr, allowed=self._def_glob_chars, case='lower', punct_replace='_')
                self._option_glob_cache[optionstr] = tmp_ret
                return tmp_ret
        else:
            try:
                return self._option_cache[optionstr]
            except KeyError:
                tmp_ret = self.slugify(optionstr, allowed=self._def_no_glob_chars, case='lower', punct_replace='_')
                self._option_cache[optionstr] = tmp_ret
                return tmp_ret

    def section_x_form(self, sectionstr, extra_allowed='_', glob=False):
        """
        Will transform the section name string as needed, by default this will slugify and uppercase the string.

        This also caches the return to minimize the times through the transformer.

        This can be overridden as desired.
        """
        if glob:
            try:
                return self._section_glob_cache[sectionstr]
            except KeyError:
                tmp_ret = self.slugify(sectionstr, allowed=self._def_glob_chars, case='upper', punct_replace='_')
                self._section_glob_cache[sectionstr] = tmp_ret
                return tmp_ret
        else:
            try:
                return self._section_cache[sectionstr]
            except KeyError:
                tmp_ret = self.slugify(sectionstr, allowed=self._def_no_glob_chars, case='upper', punct_replace='_')
                self._section_cache[sectionstr] = tmp_ret
                return tmp_ret

    def is_dot_notation(self, name):
        if self._sec_opt_sep is not None and self._sec_opt_sep in name:
            return True
        return False

    def full(self, name=_UNSET, extra_allowed=None, glob=False,
             option_or_section='option', section=_UNSET, option=_UNSET):
        tmp_check, tmp_section, tmp_option = self.both_check(name, extra_allowed=extra_allowed, glob=glob,
                                                            option_or_section=option_or_section, section=section,
                                                            option=option)
        if tmp_section is None or tmp_option is None:
            tmp_ret = None
            if tmp_section is None:
                tmp_ret = tmp_option
            elif tmp_option is None:
                tmp_ret = tmp_section
            return tmp_ret
        else:
            return '{}.{}'.format(tmp_section, tmp_option)

    def full_check(self, name=_UNSET, extra_allowed=None, glob=False,
                   option_or_section='option', section=_UNSET, option=_UNSET):

        tmp_check, tmp_section, tmp_option = self.both_check(name, extra_allowed=extra_allowed, glob=glob,
                                                             option_or_section=option_or_section,
                                                             section=section, option=option)

        if tmp_section is None or tmp_option is None or tmp_section is _UNSET or tmp_option is _UNSET:
            tmp_ret = None
            if tmp_section is None or tmp_section is _UNSET:
                tmp_ret = tmp_option
            elif tmp_option is None or tmp_option is _UNSET:
                tmp_ret = tmp_section
            return tmp_check, tmp_ret
        else:
            return tmp_check, '{}.{}'.format(tmp_section, tmp_option)

    def both(self, name=_UNSET, extra_allowed=None, glob=False,
             option_or_section='option', section=_UNSET, option=_UNSET):

        tmp_check, tmp_section, tmp_option = self.both_check(name, extra_allowed=extra_allowed, glob=glob,
                                                             option_or_section=option_or_section,
                                                             section=section, option=option)
        return tmp_section, tmp_option

    def both_check(self, name=_UNSET, extra_allowed=None, glob=False,
                   option_or_section='option', section=_UNSET, option=_UNSET):

        tmp_check = False

        if option_or_section == 'option':
            if name is None:
                return False, _UNSET, None
            tmp_option = self.option(name, extra_allowed=extra_allowed, glob=glob)
            tmp_section = self.section()
            if tmp_section is _UNSET:
                if section is not _UNSET:
                    tmp_section = self.section(section, extra_allowed=extra_allowed, glob=glob)
                else:
                    return False, _UNSET, tmp_option
            else:
                tmp_check = True
        else:
            if name is None:
                return False, None, _UNSET
            tmp_section = self.section(name, extra_allowed=extra_allowed, glob=glob)
            tmp_option = self.option()
            if tmp_option is _UNSET:
                if option is not _UNSET:
                    tmp_option = self.option(option, extra_allowed=extra_allowed, glob=glob)
                else:
                    return False, tmp_section, _UNSET
            else:
                tmp_check = True

        return tmp_check, tmp_section, tmp_option

    def option(self, option=_UNSET, extra_allowed=None, glob=False):
        if option is _UNSET:
            return self.option_x_form(self._last_option, extra_allowed=extra_allowed, glob=glob)

        if isinstance(option, str):
            if self.is_dot_notation(option):
                self._last_section = get_before(option, self._sec_opt_sep)
                return self.option_x_form(get_after(option, self._sec_opt_sep), extra_allowed=extra_allowed, glob=glob)
            else:
                self._last_section = _UNSET
                return self.option_x_form(option, extra_allowed=extra_allowed, glob=glob)
        else:
            return None

    def section(self, section=_UNSET, extra_allowed=None, glob=False):
        if section is _UNSET:
            return self.section_x_form(self._last_section, extra_allowed=extra_allowed, glob=glob)

        if isinstance(section, str):
            if self.is_dot_notation(section):
                self._last_option = get_after(section, self._sec_opt_sep)
                return self.section_x_form(get_before(section, self._sec_opt_sep),
                                           extra_allowed=extra_allowed, glob=glob)
            else:
                self._last_option = _UNSET
                return self.section_x_form(section, extra_allowed=extra_allowed, glob=glob)
        else:
            return None

    @staticmethod
    def slugify(text, delim='_', case='lower', allowed=None, punct_replace='', encode=None):
        """
        generates a simpler text string.

        :param text:
        :param delim: a string used to delimit words
        :param case: ['lower'/'upper'/'no_change']
        :param allowed: a string of characters allowed that will not be replaced.  (other than normal alpha-numeric
            which are never replaced.
        :param punct_replace: a string used to replace punction characters, if '', the characters will be deleted.
        :param encode: Will encode the result in this format.
        :return:
        """

        if text is None or not isinstance(text, str):
            return text

        punct = '[\t!"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+'
        if allowed is not None:
            for c in allowed:
                punct = punct.replace(c, '')

        result = []

        for word in text.split():
            word = normalize('NFKD', word)
            for c in punct:
                word = word.replace(c, punct_replace)
            result.append(word)

        delim = str(delim)
        # print('sluggify results: ', result)
        text_out = delim.join(result)

        if encode is not None:
            text_out.encode(encode, 'ignore')

        if case == 'lower':
            return text_out.lower()
        elif case == 'upper':
            return text_out.upper()
        else:
            return text_out

xform = Xform()


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

"""
This is a %{test of} the system



"""

def key_split(in_string, start_key, end_key=None, raise_if_no_end_key=True):
    """
    returns
    :param in_string:
    :param start_key:
    :param end_key:
    :return: before_start_key, between_start_end_key, after_end_key
    :rtype: tuple
    """
    if start_key not in in_string:
        return in_string, '', ''

    if end_key is None:
        end_key = start_key

    start_str, rem_str = in_string.split(start_key, maxsplit=1)

    if end_key not in rem_str:
        if raise_if_no_end_key:
            raise AttributeError('%s has a start key but no end key' % in_string)
        return in_string, '', ''

    mid_str, end_str = rem_str.split(end_key, maxsplit=1)

    return start_str, mid_str, end_str


def interpolate_key_check(in_string, start_key='%{', end_key='}'):
    end_str = in_string
    while end_str:
        try:
            start_str, mid_str, end_str = key_split(end_str, start_key, end_key)
        except AttributeError:
            return False
    return True


def interpolate(in_string, section, depth=0, start_key='%(', end_key=')', max_depth=10):
    if isinstance(in_string, str):
        end_str = in_string
        depth += 1

        ret_str = ''

        while end_str:

            try:
                start_str, mid_str, end_str = key_split(end_str, start_key, end_key)
            except AttributeError as err:
                raise InterpolationSyntaxError(str(err))

            if mid_str:
                mid_str = section[mid_str]

                if start_key in mid_str:
                    if depth > max_depth:
                        raise InterpolationDepthError(in_string, max_depth=max_depth, rawval=mid_str)
                    mid_str = interpolate(mid_str, section, depth=depth, start_key=start_key,
                                          end_key=end_key, max_depth=max_depth)

            ret_str += start_str + mid_str

        return ret_str
    else:
        return in_string


class BaseInterpolation:
    """Dummy interpolation that passes the value through with no changes."""

    raise_on_lookup_error = True
    replace_on_lookup_error = ''
    lookup_errors = (NoSectionError, NoOptionError)

    allow_cross_section_interpolation = True

    def __init__(self, max_depth=10, enc='()', sep='.', key='%'):

        self.max_depth = max_depth
        self.enc = enc
        self.sep = sep
        self.key = key

        # self.xform = xform

        self.key_start = enc[0]
        self.key_end = enc[1]

        # self.base_config = base_config

    def interpolatorable(self, value):
        return True

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
'''
class Interpolation_old(BaseInterpolation):
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

        # int_field_map = self.base_config

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
'''

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

        # int_field_map = self.base_config

        if not isinstance(in_string, str):
            return in_string

        return in_string.format(**section)


interpolator = Interpolation()