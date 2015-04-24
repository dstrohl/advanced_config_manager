__author__ = 'dstrohl'

import warnings
from .utils import IndentedPrinter

# log = IndentedPrinter().set_logger('CFG_MGR').set_logger_disp_level('debug')


# exception classes
class Error(Exception):
    """Base class for ConfigParser exceptions."""

    def __init__(self, msg=''):
        self.message = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.message

    __str__ = __repr__


class SimpleConfigError(Error):
    """Raised when section actions are attempted on a simple config."""

    def __init__(self, section):
        Error.__init__(self, 'No section allowed in a simple config: %r' % (section,))
        self.section = section
        self.args = (section, )


class NoSectionError(Error):
    """Raised when no section matches a requested option."""

    def __init__(self, section):
        Error.__init__(self, 'No section: %r' % (section,))
        self.section = section
        self.args = (section, )


class NoStorageManagerError(Error):
    """Raised when no storage manager matches a requested tag."""

    def __init__(self, storage_tag):
        Error.__init__(self, 'No storage manager matching: %r' % (storage_tag,))


class LockedSectionError(Error):
    """Raised when a section is locked and a change is tried."""

    def __init__(self, section):
        Error.__init__(self, 'Section Locked: %r' % (section,))
        self.section = section
        self.args = (section, )


class ForbiddenActionError(Error):
    """Raised when an action is disallowed due to configuration."""

    def __init__(self, forbidden_action_string):
        Error.__init__(self, 'Forbidden action: %s' % forbidden_action_string)


class DuplicateSectionError(Error):
    """Raised when a section is repeated in an input source.

    Possible repetitions that raise this exception are: multiple creation
    using the API or in strict parsers when a section is found more than once
    in a single input file, string or dictionary.
    """

    def __init__(self, section, source=None, lineno=None):
        msg = [repr(section), " already exists"]
        if source is not None:
            message = ["While reading from ", repr(source)]
            if lineno is not None:
                message.append(" [line {0:2d}]".format(lineno))
            message.append(": section ")
            message.extend(msg)
            msg = message
        else:
            msg.insert(0, "Section ")
        Error.__init__(self, "".join(msg))
        self.section = section
        self.source = source
        self.lineno = lineno
        self.args = (section, source, lineno)


class DuplicateCLIOptionError(Error):
    def __init__(self, option, cli_arg):
        msg = '%s from option %s already exists' % option, cli_arg
        Error.__init__(self, msg)


class DuplicateOptionError(Error):
    """Raised by strict parsers when an option is repeated in an input source.

    Current implementation raises this exception only when an option is found
    more than once in a single file, string or dictionary.
    """

    def __init__(self, section, option, source=None, lineno=None):
        msg = [repr(option), " in section ", repr(section),
               " already exists"]
        if source is not None:
            message = ["While reading from ", repr(source)]
            if lineno is not None:
                message.append(" [line {0:2d}]".format(lineno))
            message.append(": option ")
            message.extend(msg)
            msg = message
        else:
            msg.insert(0, "Option ")
        Error.__init__(self, "".join(msg))
        self.section = section
        self.option = option
        self.source = source
        self.lineno = lineno
        self.args = (section, option, source, lineno)


class NoOptionError(Error):
    """A requested option was not found."""

    def __init__(self, option, section):
        Error.__init__(self, "No option %r in section: %r" %
                       (option, section))
        self.option = option
        self.section = section
        self.args = (option, section)


class EmptyOptionError(Error):
    """A requested option was found but did not have a value or default value."""

    def __init__(self, option, section):
        Error.__init__(self, "Option %r in section %r found with no value and no default" %
                       (option, section))
        self.option = option
        self.section = section
        self.args = (option, section)


class ParsingError(Error):
    """Raised when a configuration file does not follow legal syntax."""

    def __init__(self, source=None, filename=None):
        # Exactly one of `source'/`filename' arguments has to be given.
        # `filename' kept for compatibility.
        if filename and source:
            raise ValueError("Cannot specify both `filename' and `source'. "
                             "Use `source'.")
        elif not filename and not source:
            raise ValueError("Required argument `source' not given.")
        elif filename:
            source = filename
        Error.__init__(self, 'Source contains parsing errors: %r' % source)
        self.source = source
        self.errors = []
        self.args = (source, )

    @property
    def filename(self):
        """Deprecated, use `source'."""
        warnings.warn(
            "The 'filename' attribute will be removed in future versions.  "
            "Use 'source' instead.",
            DeprecationWarning, stacklevel=2
        )
        return self.source

    @filename.setter
    def filename(self, value):
        """Deprecated, user `source'."""
        warnings.warn(
            "The 'filename' attribute will be removed in future versions.  "
            "Use 'source' instead.",
            DeprecationWarning, stacklevel=2
        )
        self.source = value

    def append(self, lineno, line):
        self.errors.append((lineno, line))
        self.message += '\n\t[line %2d]: %s' % (lineno, line)


class MissingSectionHeaderError(ParsingError):
    """Raised when a key-value pair is found before any section header."""

    def __init__(self, filename, lineno, line):
        Error.__init__(
            self,
            'File contains no section headers.\nfile: %r, line: %d\n%r' %
            (filename, lineno, line))
        self.source = filename
        self.lineno = lineno
        self.line = line
        self.args = (filename, lineno, line)

