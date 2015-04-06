__author__ = 'dstrohl'

__all__ = ['_UNSET', 'UnSet']


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

    def __hash__(self):
        return hash('__UnSet_Object__')


_UNSET = UnSet()
