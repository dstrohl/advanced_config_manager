__author__ = 'dstrohl'

from AdvConfigMgr.utils import interpolate, validate_interpolation_str

__all__ = ['Interpolation', 'NoInterpolation']


class BaseInterpolation:
    """Dummy interpolation that passes the value through with no changes."""

    def __init__(self, key='%', sep='.', enc='()', max_depth=10):
        self.key = key
        self.sep = sep
        self.enc = enc
        self.max_depth = max_depth

    def interpolatorable(self, value):
        key_str = self.key+self.enc[0]
        if isinstance(value, str) and key_str in value:
            return True
        else:
            return False

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


class NoInterpolation(BaseInterpolation):

    def interpolatorable(self, value):
        return False


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
