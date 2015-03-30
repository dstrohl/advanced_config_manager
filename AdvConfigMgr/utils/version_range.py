__author__ = 'dstrohl'

from distutils.version import LooseVersion


class VersionRange(object):

    def __init__(self, version_class=None, sup_ver=None, min_ver=None, max_ver=None):
        if version_class is None:
            self._version_class = LooseVersion
        else:
            self._version_class = version_class

        self.ver_is = self._make_ver(sup_ver)
        self.ver_min = self._make_ver(min_ver)
        self.ver_max = self._make_ver(max_ver)

        if self.ver_is is not None:
            if self.ver_min is not None and not self._contains(self.ver_min, self.ver_is):
                raise AttributeError('Min Version is not inside super Version')
            if self.ver_max is not None and not self._contains(self.ver_max, self.ver_is):
                raise AttributeError('Max Version is not inside super Version')

    def _contains(self, other, container):

        """
        other in container
        3.4.5 in 3.4
        true

        3.1.0 in 3.4
        false

        3.4 in 3.4.1
        False


        """
        if isinstance(other, str):
            other = self._make_ver(other)

        other = self._stripped(other)
        container = self._stripped(container)

        if len(other) < len(container):
            return False

        for s, o in zip(container, other):
            try:
                if s < o:
                    return False
            except TypeError:
                return False
        return True

    @staticmethod
    def _stripped(version):
        """
        returns a version without any trailing zeros
        """
        new_len = len(version.version)
        for pos, num in enumerate(reversed(version.version)):
            if num != 0:
                return version.version[:new_len-pos]
        return []

    def _make_ver(self, ver):
        if ver is None:
            return ver
        if isinstance(ver, str):
            return self._version_class(ver)
        if isinstance(ver, type(self._version_class)):
            return ver
        return self._version_class(str(ver))

    def __cmp__(self, other):
        other = self._make_ver(other)
        if other in self:
            return 0
        if other < self.ver_min:
            return -1
        if other > self.ver_max:
            return 1



    def lt(self, other):
        other = self._make_ver(other)
        if self.ver_min is not None:
            return other < self.ver_min

        if self.ver_is is not None:
            return other < self.ver_is

        return False

    def gt(self, other):
        other = self._make_ver(other)
        if self.ver_max is not None and other > self.ver_max:
            return True
        if other in self:
            return False
        return True

    def le(self, other):
        other = self._make_ver(other)
        if self.ver_min and other == self.ver_min:
            return True
        if other < self.ver_min:
            return True
        if self.ver_is and other == self.ver_is:
            return True
        else:
            return False

    def ge(self, other):
        other = self._make_ver(other)
        if self.ver_max:
            return other >= self.ver_max
        else:
            raise Warning('Comparing versions with "Greater than" without a max set may not result in expected results.')
            return False

    def __contains__(self, item):
        item = self._make_ver(item)
        if self.ver_is is not None:
            if not self._contains(item, self.ver_is):
                return False
        if self.ver_min is not None:
            if item < self.ver_min:
                return False
        if self.ver_max is not None:
            if item > self.ver_max:
                return False
        return True

    def __repr__(self):
        return 'Version Range [{}] / [{} - {}]'.format(self.ver_is, self.ver_min, self.ver_max)