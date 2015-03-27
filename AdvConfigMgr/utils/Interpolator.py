__author__ = 'dstrohl'

__all__ = ['interpolate', 'validate_interpolation_str']

from AdvConfigMgr.utils import Error, get_between, get_after, MultiLevelDictManager


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


def validate_interpolation_str(in_string,
                               key='%',
                               key_enc='()'):
    """
    validates that the string passed does not have major structural errors.  This does not validate that any
    interpolation keys exist in any given field_map.

    :param in_string: the string to check
    :param key: the key used
    :param key_enc: the seperators used
    :return: in_string if passed.  raises InterpolationSyntaxError if not.
    """

    if not isinstance(in_string, str):
        return in_string

    if key not in in_string:
        return in_string

    key_start = key_enc[0]
    key_end = key_enc[1]

    rest = in_string
    accum = []

    while rest:
        key_pos = rest.find(key)
        if key_pos < 0:
            return

        if key_pos >= 0:
            accum.append(rest[:key_pos])
            rest = rest[key_pos:]

        c = rest[1:2]
        if c == key:
            accum.append(key)
            rest = rest[2:]

        elif c == key_start:

            if key_end not in rest:
                raise InterpolationSyntaxError("bad interpolation variable reference %r" % rest)

            rest = get_after(rest, key_end)

        else:
            raise InterpolationSyntaxError(
                "'{0}' must be followed by '{0}' or '{2}', found: {1}".format(key, rest, key_start))

    return in_string


def interpolate(in_string,
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
    """

    Interpolator Engine:

    This will interpolate key strings from a passed string by looking them up in a dictionary.  The dictionary can be
    multi leveled and strings can be passed as a path string (i.e. '.path1.path2.path3.dict_key')

    .. note:: If a non string is passed, it is returned with no changes.

    :param in_string: the initial string to parse, if this is not a string, we will return it as it is with no
        processing.
    :param field_map: a dictionary (or dict like object), or dict of dict's that to be used for lookups.
    :param depth: the current recursive depth
    :param max_depth: the max recursive depth
    :param key: Default: "%", The char used to identify the key string
    :param key_sep: Default: ".", The seperator used in the case of a multi-level lookup
    :param key_enc: Default: "()", Defines the enclosure that the keys will be in.  this needs to be a 2 char string,
        with the characters being the first and last character of the enclosure.  these cannot be duplicates and cannot
        be characters that will show up in the string.  examples:  "()" or "{}" or "[]".
    :param on_key_error: ['raise'/'skip'/'replace'] controls how to handle lookup errors.
    :param error_replace: replace the key with this string if there is an error
    :param errors_to_except: allows for over-riding the list of errors to accept if custom errors are defined
    :return:  the final interpolated string.
    """
    int_field_map = MultiLevelDictManager(field_map, current_path, key_sep)

    if not isinstance(in_string, str):
        return in_string

    if key not in in_string:
        return in_string

    key_start = key_enc[0]
    key_end = key_enc[1]

    rest = in_string
    accum = []

    recursive_path = ''

    if errors_to_except is None:
        errors_to_except = (KeyError,)

    if depth > max_depth:
        raise InterpolationDepthError(in_string, max_depth, rest)

    while rest:
        key_pos = rest.find(key)
        if key_pos < 0:
            return

        if key_pos >= 0:
            accum.append(rest[:key_pos])
            rest = rest[key_pos:]
        # p is no longer used

        c = rest[1:2]
        if c == key:
            accum.append(key)
            rest = rest[2:]

        elif c == key_start:

            if key_end not in rest:
                raise InterpolationSyntaxError("bad interpolation variable reference %r" % rest)

            m = get_between(rest, key_start, key_end)

            if on_key_error == 'raise':
                key_value = int_field_map[m]
                recursive_path = int_field_map.path.new_path(m)
            else:
                try:
                    key_value = int_field_map[m]
                    recursive_path = int_field_map.path.new_path(m)

                    # key_value = ml_dict(field_map, m, key_sep, current_path)

                except errors_to_except:
                    if on_key_error == 'skip':
                        key_value = ''
                    else:
                        key_value = error_replace

            if key in key_value:
                key_value = interpolate(key_value, field_map,
                                        depth=depth+1,
                                        max_depth=max_depth,
                                        key=key,
                                        key_sep=key_sep,
                                        key_enc=key_enc,
                                        current_path=recursive_path,
                                        on_key_error=on_key_error,
                                        error_replace=error_replace,
                                        errors_to_except=errors_to_except)

            accum.append(key_value)

            rest = get_after(rest, key_end)

        else:
            raise InterpolationSyntaxError(
                "'{0}' must be followed by '{0}' or '{2}', found: {1}".format(key, rest, key_start))

    return ''.join(accum)
