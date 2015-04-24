__author__ = 'dstrohl'


from .base_utils import list_in_list

# ===============================================================================
# Flag Manager
# ===============================================================================


class FlagList(object):
    def __init__(self):
        self._flags = []

    def add(self, flag):
        if flag not in self._flags:
            self._flags.append(flag)

    def rem(self, flag):
        if flag in self._flags:
            self._flags.remove(flag)

    def __contains__(self, item):
        return item in self._flags

    def __bool__(self):
        if self._flags:
            return True
        else:
            return False

    def __call__(self, add_rem_flags=None):
        add_rem_flags = add_rem_flags.replace(',', ' ')
        add_rem_flags = add_rem_flags.replace(';', ' ')
        if add_rem_flags:
            tmp_flags = add_rem_flags.split()
            for f in tmp_flags:
                if f[0] == '-':
                    self.rem(f[1:])
                elif f[0] == '+':
                    self.add(f[1:])
                else:
                    self.add(f)
        return self._flags

    def __str__(self):
        return ', '.join(self._flags)


    def __iter__(self):
        for r in self._flags:
            yield r

    def __len__(self):
        return len(self._flags)

class Flagger(object):
    def __init__(self):
        self._include = FlagList()
        self._exclude = FlagList()
        self._current = FlagList()

    @property
    def inc(self):
        return self._include

    @property
    def exc(self):
        return self._exclude

    @property
    def cur(self):
        return self._current

    @property
    def check(self):
        tmp_ret = False
        if self.inc:
            if list_in_list(self.cur, self.inc):
                tmp_ret = True
        else:
            tmp_ret = True

        if self.exc:
            if list_in_list(self.cur, self.exc):
                tmp_ret = False
        return tmp_ret

    def __call__(self, current=None, include=None, exclude=None, **kwargs):
        if kwargs:
            current = kwargs.get('c', current)
            include = kwargs.get('i', include)
            exclude = kwargs.get('e', exclude)
        if current:
            self.cur(current)
        if include:
            self.inc(include)
        if exclude:
            self.exc(exclude)

        return self.check
