__author__ = 'dstrohl'

# from CompIntel.Core.Config.config_exceptions import NoOptionError, NoSectionError, Error
from PythonUtils import IndentedPrinter, interpolate, validate_interpolation_str

__all__ = ['Interpolation']

ip = IndentedPrinter()


'''
class InterpolationMissingOptionError(InterpolationError):
    """A string substitution required a setting which was not available."""

    def __init__(self, option, section, rawval, reference):
        msg = ("Bad value substitution:\n"
               "\tsection: [%s]\n"
               "\toption : %s\n"
               "\tkey    : %s\n"
               "\trawval : %s\n"
               % (section, option, reference, rawval))
        InterpolationError.__init__(self, option, section, msg)
        self.reference = reference
        self.args = (option, section, rawval, reference)
'''




"""
from the option class
    @property
    def get_stored_value(self):
        if self.has_set_value:
            return self._value
        elif self.has_default_value and self._section.store_default:
            return self.default_value

    @property
    def get_storage_string(self):
        return self._validator.to_string(self.get_stored_value)

    def set_value_from_string(self, value, force=True):
        if not self.do_not_change or force:
            self._value = self._validator.from_string(value)
"""


# _KEYCRE = re.compile(r"%\(([^)]+)\)")



'''
class BaseInterpolation:
    """Dummy interpolation that passes the value through with no changes."""

    def before_get(self, parser, section, option, value):
        return value

    def before_set(self, parser, section, option, value):
        return value

    def before_read(self, parser, section, option, value, as_string=False):
        if not as_string:
            return value
        else:
            return parser[section][option].from_string(value)

    def before_write(self, parser, section, option, value, as_string=False):
        if not as_string or isinstance(value, str):
            return value
        else:
            return parser[section][option].to_string(value)
'''

class BaseInterpolation:
    """Dummy interpolation that passes the value through with no changes."""

    def before_get(self, config_root, section_name, value):
        """
        run on value returned from the config_root before returning it to the calling system.

        .. note:: this is the main interpolation location.

        :param config_root: a link to the base config_root
        :param section_name: the name of the current section
        :param value: the value from the config root
        :return: the value to be returned
        """
        return value

    def before_set(self, config_root, section_name, value):
        """
        run on values before saving them to the config_root from the calling system

        .. note:: Normally used to validate any interpolation keys

        :param config_root: the config root
        :param section_name: the name of the current section
        :param value: the value to be saved
        :return: the interpolated value to be saved to the config_root
        """
        return value

    def before_read(self, config_root, section_name, value):
        """
        run on values after they are returned from storage and before they are saved to the config_root

        .. note:  Normally not used.

        :param config_root: the config root
        :param section_name: the name of the current section
        :param value: the value from storage
        :return: the value to save to the config_root
        """
        return value

    def before_write(self, config_root, section_name, value):
        """
        run on values after they are returned from config_root and before they are saved to storage

        .. note: Normally not used.

        :param config_root: the config root
        :param section_name: the name of the current section
        :param value: the value from the config_root
        :return: the value to save to the config_root
        """
        return value


class Interpolation(BaseInterpolation):
    key = '%'
    sep = '.'
    max_depth = 10
    enc = '()'



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

    def __init__(self, key=key, sep=sep, enc=enc):
        self.key = key
        self.sep = sep
        self.enc = enc

    def before_get(self, config_root, section_name, value):
        return interpolate(value,
                           config_root,
                           max_depth=self.max_depth,
                           key=self.key,
                           key_sep=self.sep,
                           key_enc=self.enc,
                           current_path=section_name)

    def before_set(self, config_root, section_name, value):
        return validate_interpolation_str(value, self.key, self.enc)

'''
class Interpolation(BaseInterpolation):
    INTERPOLATION_KEY = '%'
    SECTION_OPTION_SEP = '.'
    ESCAPED_KEY = INTERPOLATION_KEY+INTERPOLATION_KEY
    
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

    #: TODO remove "defaults" and validate code
    #: TODO add datatype and force_string

    _KEYCRE = re.compile(r"%\(([^)]+)\)s")

    def __init__(self, key=None, sep=None):
        if key is not None:
            self.INTERPOLATION_KEY = key
            self.ESCAPED_KEY = key+key
        if sep is not None:
            self.SECTION_OPTION_SEP = sep
        else:
            self.SECTION_OPTION_SEP = ('.', ':')

    def before_get(self, parser, section, option, value):
        L = []
        self._interpolate_some(parser, option, L, value, section, 1)
        return ''.join(L)

    def before_set(self, parser, section, option, value):
        tmp_value = value.replace(self.ESCAPED_KEY, '')  # escaped percent signs
        tmp_value = self._KEYCRE.sub('', tmp_value)  # valid syntax
        if self.INTERPOLATION_KEY in tmp_value:
            raise ValueError("invalid interpolation syntax in %r at "
                             "position %d" % (value, tmp_value.find(self.INTERPOLATION_KEY)))
        return value

    def _interpolate_some(self, parser, option, accum, rest, section, map,
                          depth):
        if depth > MAX_INTERPOLATION_DEPTH:
            raise InterpolationDepthError(option, section, rest)
        while rest:
            p = rest.find(self.INTERPOLATION_KEY)
            if p < 0:
                accum.append(rest)
                return
            if p > 0:
                accum.append(rest[:p])
                rest = rest[p:]
            # p is no longer used
            c = rest[1:2]
            if c == self.INTERPOLATION_KEY:
                accum.append(self.INTERPOLATION_KEY)
                rest = rest[2:]
            elif c == "{":
                m = self._KEYCRE.match(rest)
                if m is None:
                    raise InterpolationSyntaxError(option, section,
                                                   "bad interpolation variable reference %r" % rest)
                path = m.group(1).split(self.SECTION_OPTION_SEP)
                rest = rest[m.end():]
                sect = section
                opt = option
                try:
                    if len(path) == 1:
                        opt = parser.optionxform(path[0])
                        v = map[opt]
                    elif len(path) == 2:
                        sect = path[0]
                        opt = parser.optionxform(path[1])
                        v = parser.get(sect, opt, raw=True)
                    else:
                        raise InterpolationSyntaxError(
                            option, section,
                            "More than one %s found: %r" % (self.SECTION_OPTION_SEP, rest))
                except (KeyError, NoSectionError, NoOptionError):
                    raise InterpolationMissingOptionError(
                        option, section, rest, self.SECTION_OPTION_SEP.join(path))
                if self.INTERPOLATION_KEY in v:
                    self._interpolate_some(parser, opt, accum, v, sect,
                                           dict(parser.items(sect, raw=True)),
                                           depth + 1)
                else:
                    accum.append(v)
            else:
                raise InterpolationSyntaxError(
                    option, section,
                    "'{1}' must be followed by '{1}' or '{', "
                    "found: {2}".format(self.INTERPOLATION_KEY, rest))

'''
'''
class ExtendedInterpolation(Interpolation):
    """Advanced variant of interpolation, supports the syntax used by
    `zc.buildout'. Enables interpolation between sections."""

    _KEYCRE = re.compile(r"\$\{([^}]+)\}")

    def before_get(self, parser, section, option, value, defaults):
        L = []
        self._interpolate_some(parser, option, L, value, section, defaults, 1)
        return ''.join(L)

    def before_set(self, parser, section, option, value):
        tmp_value = value.replace('$$', '')  # escaped dollar signs
        tmp_value = self._KEYCRE.sub('', tmp_value)  # valid syntax
        if '$' in tmp_value:
            raise ValueError("invalid interpolation syntax in %r at "
                             "position %d" % (value, tmp_value.find('$')))
        return value

    def _interpolate_some(self, parser, option, accum, rest, section, map,
                          depth):
        if depth > MAX_INTERPOLATION_DEPTH:
            raise InterpolationDepthError(option, section, rest)
        while rest:
            p = rest.find("$")
            if p < 0:
                accum.append(rest)
                return
            if p > 0:
                accum.append(rest[:p])
                rest = rest[p:]
            # p is no longer used
            c = rest[1:2]
            if c == "$":
                accum.append("$")
                rest = rest[2:]
            elif c == "{":
                m = self._KEYCRE.match(rest)
                if m is None:
                    raise InterpolationSyntaxError(option, section,
                                                   "bad interpolation variable reference %r" % rest)
                path = m.group(1).split(':')
                rest = rest[m.end():]
                sect = section
                opt = option
                try:
                    if len(path) == 1:
                        opt = parser.optionxform(path[0])
                        v = map[opt]
                    elif len(path) == 2:
                        sect = path[0]
                        opt = parser.optionxform(path[1])
                        v = parser.get(sect, opt, raw=True)
                    else:
                        raise InterpolationSyntaxError(
                            option, section,
                            "More than one ':' found: %r" % (rest,))
                except (KeyError, NoSectionError, NoOptionError):
                    raise InterpolationMissingOptionError(
                        option, section, rest, ":".join(path))
                if "$" in v:
                    self._interpolate_some(parser, opt, accum, v, sect,
                                           dict(parser.items(sect, raw=True)),
                                           depth + 1)
                else:
                    accum.append(v)
            else:
                raise InterpolationSyntaxError(
                    option, section,
                    "'$' must be followed by '$' or '{', "
                    "found: %r" % (rest,))


class LegacyInterpolation(Interpolation):
    """Deprecated interpolation used in old versions of ConfigParser.
    Use BasicInterpolation or ExtendedInterpolation instead."""

    _KEYCRE = re.compile(r"%\(([^)]*)\)s|.")

    def before_get(self, parser, section, option, value, vars):
        rawval = value
        depth = MAX_INTERPOLATION_DEPTH
        while depth:  # Loop through this until it's done
            depth -= 1
            if value and "%(" in value:
                replace = functools.partial(self._interpolation_replace,
                                            parser=parser)
                value = self._KEYCRE.sub(replace, value)
                try:
                    value = value % vars
                except KeyError as e:
                    raise InterpolationMissingOptionError(
                        option, section, rawval, e.args[0])
            else:
                break
        if value and "%(" in value:
            raise InterpolationDepthError(option, section, rawval)
        return value

    def before_set(self, parser, section, option, value):
        return value

    @staticmethod
    def _interpolation_replace(match, parser):
        s = match.group(1)
        if s is None:
            return match.group()
        else:
            return "%%(%s)s" % parser.optionxform(s)
'''