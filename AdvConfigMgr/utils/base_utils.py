__author__ = 'dstrohl'
"""
A collection of simple(ish) functions and classes.
"""

__all__ = ['args_handler', 'GenericMeta', 'DictKey2Method', 'AdvDict', 'DBList', 'UnSet',
           'TreeDict', 'TreeItem', 'make_list', 'flatten', 'unpack_class_method', 'get_between', 'get_after',
           'get_before', 'get_not_in', 'get_same', 'get_meta_attrs', 'remove_dupes', 'list_in_list', 'list_not_in_list',
           'count_unique', 'index_of_count', 'ListPlus', 'LookupManager', 'is_iterable', 'is_string', 'Error', 'Path',
           'OrderedSet', 'swap', 'replace_between', 'format_as_decimal_string', 'MultiLevelDictManager',
           'elipse_trim', 'concat', 'generate_percentages', 'convert_to_boolean', 'slugify', 'merge_dictionaries']

import copy
import sys
import collections
from string import Formatter
from decimal import Decimal



# ===============================================================================
# Error Class
# ===============================================================================

class Error(Exception):
    """Base class for custom exceptions."""

    def __init__(self, msg=''):
        self.message = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.message

    __str__ = __repr__


# ===============================================================================
# UnSet Class
# ===============================================================================

class UnSet(object):
    """
    Used in places to indicated an unset condition where None may be a valid option

    .. note:: *I borrowed the concept from* :py:mod:`configparser` *module*
    
    Example:
        For an example of this, see :py:class:`MultiLevelDictManager.get`
    
    """
    UnSetValidationString = '_*_This is the Unset Object_*_'

    def __repr__(self):
        return 'Empty Value'

    def __str__(self):
        return 'Empty Value'

    def __get__(self):
        return str(self)

    def __eq__(self, other):
        return isinstance(other, UnSet)


_UNSET = UnSet()

# ===============================================================================
# Path Class
# ===============================================================================


class Path(object):
    """
    A class for managing a path, this could be a file path, but it is more aimed at a path through modules
    or dictionaries.

    Path strings:

    ================    ===========================     ========================================
    Path String         Current                         Result
    ================    ===========================     ========================================
    'p3.p4.p5.thing'    Path: 'p1.p1' Item: ''          Path: 'p1.p2.p3.p4.p5'  Item: 'thing'
    '.p1.p2.thing'      Path: 'p3.p4' Item: 'thing'     Path: 'p1.p2'  Item: 'thing'
    '.p1.p2.'           Path: 'p3.p4' Item: 'thing'     Path: 'p1.p2'  Item: 'thing'
    '.'                 Path: 'p3.p4' Item: 'thing'     Path: ''    Item: 'thing'
    'thing'             Path: 'p3.p4' Item: ''          Path: 'p3.p4'  Item: 'thing'
    ================    ===========================     ========================================

    Examples:


        p = path()


    """

    def __init__(self, current_path='', cd='', key_sep='.'):
        """
        :param current_path: The current path to be set, this can be a text string, or it can be another :class:`path`
            object
        :param cd:
        :param key_sep:
        :return:
        """
        self._pwd = []
        self.item = ''
        self.key_sep = key_sep
        #: TODO Shortcut current path
        self.cd(current_path)
        self.cd(cd)

    def cd(self, new_path):

        if isinstance(new_path, Path):
            new_path = new_path.path_str(self.key_sep, full=True)

        if new_path == '':
            pass
        elif new_path == self.key_sep:
            # if the new path is root
            self._pwd = []
        elif new_path[0] == self.key_sep and new_path[1] != self.key_sep:
            # if the new path starts at the root
            parse_key = new_path[1:]
            self._pwd = parse_key.split(self.key_sep)
            tmp_item = self._pwd.pop()
            if tmp_item != '':
                self.item = tmp_item
        else:
            if new_path[0] == self.key_sep:
                # if the new path starts with a seperator
                new_path = new_path[1:]
                while new_path[0] == self.key_sep:
                    # if there are multiple seperators
                    if len(self) > 0:
                        self._pwd.pop()
                    new_path = new_path[1:]
                    if new_path == '':
                        break

            self._pwd.extend(new_path.split(self.key_sep))
            tmp_item = self._pwd.pop()
            if tmp_item != '':
                self.item = tmp_item

        return self

    def cwd(self, new_path):
        """
        will change the working directory, but will assume that there is a trailing key_sep
        (so, assuming there is no item).

        this is a helper method for cd.
        :param new_path: new path
        """
        if new_path.endswith(self.key_sep):
            return self.cd(new_path)
        else:
            new_path += self.key_sep
            return self.cd(new_path)

    @property
    def pwd(self):
        """
        returns the present working directory list
        :return:
        """
        return self._pwd

    @property
    def path_list(self):
        """
        returns the current path as a list object of path and item.
        :return:
        """
        tmp_ret = []
        tmp_ret.extend(self._pwd)
        if self.item != '':
            tmp_ret.append(self.item)
        return tmp_ret

    def new_path(self, cd='', key_sep=None):
        """
        Creates an new path object from this one
        :param cd: change directory of new object
        :param key_sep: new key seperator
        """
        if key_sep is None:
            key_sep = self.key_sep

        return Path(self, cd, key_sep)

    def path_str(self, key_sep=None, full=False, inc_item=True):
        """
        returns the current path as a string.

        :param key_sep: allows setting the key_sep for the string
        :param full: if True will return the full path, including a leading sep and final key_sep if needed.
        :param inc_item: if set False will only return the path, not the item.
        """
        if key_sep is None:
            key_sep = self.key_sep

        tmp_ret = ''

        if inc_item and self.item == '':
            inc_item = False

        if full:
            tmp_ret += key_sep

        tmp_ret += key_sep.join(self.pwd)

        if full or inc_item:
            tmp_ret += key_sep
            if inc_item:
                tmp_ret += self.item
                # if full:
                # tmp_ret += key_sep
        return tmp_ret


    def __call__(self, new_path=''):
        return self.cd(new_path)

    def __str__(self):
        return self.path_str()

    def __len__(self):
        if self.item == '':
            return len(self._pwd)
        else:
            return len(self.pwd) + 1

    def __getitem__(self, item):
        if isinstance(item, int):
            if item > len(self._pwd):
                return self.item
            else:
                return self._pwd[item]
        else:
            raise TypeError('path indices must be integers')

    def __iter__(self):
        for i in self._pwd:
            yield i
        yield self.item

    def __eq__(self, other):
        if isinstance(other, str):
            tmp_path = Path(other)
        elif isinstance(other, Path):
            tmp_path = other
        else:
            raise TypeError('compared items must be either string or path object')
        if tmp_path._pwd == self._pwd and tmp_path.item == self.item:
            return True
        else:
            return False

    def __bool__(self):
        if self._pwd == [] and self.item == '':
            return False
        else:
            return True

    __repr__ = __str__


def merge_dictionaries(*args, depth=0, max_depth=10):
    tmp_out_dict = {}

    if depth == max_depth:
        raise AttributeError('Merge dictionaries recussion depth max reached!')

    for arg in args:
        if is_iterable(arg):
            depth += 1
            tmp_out_dict.update(merge_dictionaries(arg, depth))

        elif isinstance(arg, dict):
            tmp_out_dict.update(arg)

        else:
            raise TypeError('Merge dictionaries only accepts iterables of dictionaries')

    return tmp_out_dict


class MultiLevelDictManager(object):
    """
    This provides a dictionary view that can be accessed via a :py:class:`Path` object or string.
    
    Examples:
        >>> mld = MultiLevelDictManager()
    
        >>> test_dict = {
                'level': '1',
                'l2a': {
                    'level': '2a',
                    'l3aa': {
                        'level': '3aa',
                        'l4aaa': {'level': '4aaa'},
                        'l4aab': {'level': '4aab'}},
                    'l3ab': {
                        'level': '3ab',
                        'l4aba': {'level': '4aba'},
                        'l4abb': {'level': '4abb'}}},
                'l2b': {
                    'level': '2b',
                    'l3ba': {
                        'level': '3ba',
                        'l4baa': {'level': '4baa'},
                        'l4bab': {'level': '4bab'}},
                    'l3bb': {
                        'level': '3bb',
                        'l4bba': {'level': '4bba'},
                        'l4bbb': {'level': '4bbb'}}}
                }
 

        >>> mldm = MultiLevelDictManager(test_dict)

        >>> mldm.cd['level']
        1
        
        >>>mldm['.l2a.level']
        '2a'

        >>>mldm('.l2a.')
        >>>mldm.get('level')
        '2a'

        >>>mldm.cd('.l2b.l3bb')
        >>>mldm['..level']
        '2b'

        >>>mldm.cd('.l2b.l3bb.l4bbb')
        >>>mldm['....level']
        '1'

        >>>mldm.cd('.l2b.l3bb.14bbb')
        >>>mldm['......level']
        '1'

        >>>mldm.cd('.l2b.l3bb.l4bbb')
        >>>mldm.get('......leddvel', 'noanswer')
        'noanswer'

        >>>mldm.cd('.l2b.l3bb.l4bbb')
        >>>mldm.pwd
        'l2b.l3bb.l4bbb'

        >>>mldm.cd('.')
        >>>mldm.get('l2b.l3bb.l4bbb.level', cwd=True)
        '4bbb'
        
        >>>mldm.get('..level', cwd=True)
        '3bb'

    
    """
    dict_db = None
    key_sep = '.'

    def __init__(self,
                 dict_db=None,
                 current_path='',
                 key_sep='.'):
        """
        :param dict_db: the dictionary to use for lookups.  The keys for this must be strings.
        :param current_path: the current path string (see :py:class:`Path` for more info on path strings)
        :param key_sep: the string to use to seperate the keys in the path, by default '.'
        """
        self.dict_db = dict_db
        if isinstance(current_path, str):
            current_path += key_sep
        self.path = Path(current_path, key_sep=key_sep)
        # self.key_sep = key_sep

    def load(self,
             dict_db,
             current_path=''):
        """
        Allows you to load a new dictionary, the path will be reset unless passed
        :param dict_db: The new dictionary for lookups
        :param current_path: The new path to use (will be reset to '.' unless passed)
        """
        self.dict_db = dict_db
        self.path(current_path)

    def cd(self, key):
        """
        Change directory path to a new path string (key)

        :param key: the new path string to chance to, see :py:class:`Path` for info on path strings
        :return:
        """
        self.cd(key)
        # self._pwd = self._parse_full_path(key)

    def get(self, key, default=_UNSET, cwd=False):
        """
        will get the data from the specified path string
        
        :param key: The path string to use (see :py:class:`Path` for info on path strings)
        :param default: if passed, a default to return if the key is not found at any level.
        :param cwd: Will change the current path to the path of the key passed.
        """

        cur_resp = self.dict_db
        tmp_path = Path(self.path, key)
        # key_path = self._parse_full_path(key)

        for k in tmp_path:
            try:
                cur_resp = cur_resp[k]
            except KeyError:
                if default is not _UNSET:
                    return default
                else:
                    msg = 'Key: "{}" not found in dict: {}'.format(k, self.dict_db)
                    raise KeyError(msg)
            except TypeError:
                msg = "parameter passed is not a dict or does not implement key lookups"
                raise TypeError(msg)

        if cwd:
            self.path = tmp_path

        return cur_resp

    def cwd(self, key):
        """
        Changes the current working directory to the passed path string (key).
        
        This is a shortcut for having to pass a path with a '.' at the end to signify a path
        
        :param key: The path string to use (see :py:class:`Path` for info on path strings)
        """
        self.path.cwd(key)


    @property
    def pwd(self):
        """
        Returns the current working directory and item (if present)
        """

        return self.path.path_str()
        # return self.key_sep.join(self._pwd)

    def __getitem__(self, item):
        return self.get(item)

    def __repr__(self):
        return 'MultiLevelLookupDict: current_path:{}  Dict:{}'.format(self.path, self.dict_db)

    __call__ = get


# ===============================================================================
# Generate Percentages
# ===============================================================================


def generate_percentages(data_array, row_fieldname, data_fieldname, newfieldname=""):
    '''

    Computes percentage of the total column per item and adds it to the array (or replaces an existing field.)

    assumes data_array will be in the format of:
    ::
        [
        { 'row_fieldname' : [{field1:data1, field2,data2, field3:data3},{field1:data1, field2,data2, field3:data3},{field1:data1, field2,data2, field3:data3}]}
    
        ]
    ::
    
    * if no newfieldname, fieldname is replaced with percentages
    * if fieldnames are numeric, a set is assumed instead of a dict
    * if new_fieldname is numeric, the data will be inserted at that position (zero based).
    '''

    for col in range(len(data_array[1][row_fieldname])):

        col_total = 0
        # print('new col')
        for row in range(len(data_array)):
            rec = data_array[row][row_fieldname][col]
            # print( rec )
            col_total = col_total + rec[data_fieldname]
            # print(col_total)

        for row in range(len(data_array)):
            rec = data_array[row][row_fieldname][col][data_fieldname]
            try:
                rec_perc = rec / col_total
            except ZeroDivisionError:
                rec_perc = 0

            if newfieldname:
                data_array[row][row_fieldname][col][newfieldname] = rec_perc
            else:
                data_array[row][row_fieldname][col][data_fieldname] = rec_perc


                # print( rec_perc )

    # print(data_array)

    return data_array


# ===============================================================================
# Argument Handler
# ===============================================================================


def args_handler(parent_obj,
                 args=None,
                 attr_list=None,
                 kwargs=None,
                 skip_list=None,
                 skip_startswith='-',
                 overwrite=True,
                 do_not_check_parent_attrs=False):
    """
    Args Handler that will take an args or kwargs list and set contents as attributes.  This also allows some control
    over which values to set.

    This can be used when creating that may need to take different types of arguments as it can intelligently detect
    fields passed as arguments, keyword arguments, or a dictionary of arguments, it can handle required arguments as
    as well as long lists of arguments very simply.

    Parameters:
        parent_obj: the object that gets the attributes
        args: a list from the args parameter
        kwargs: a dict from the kwargs parameter
        attr_list: a list of the attributes to use, required if args are passed

            .. note::
                * if the attribute '_attr_list' exists in the parent object, this will be used.
                * if an attr_list exists for kwargs dicts, only the keys in the args list will be included.
                * if there are more items in the args list than in the attr list, only the ones in the list will be used.
                * if there are more items in the attr list than in the args list, only the ones in the args list will be used.
                * if both args and kwargs are passed, the attr list will ONLY be used for the args
                * if the same attr is in both args and kwargs, kwargs will take precedence.
                * if the attribute name starts with a \*, (star) it will be required and a AttributeError will be raised
                    if it is not found in either the args or kwargs.
                * if a list of tuples can be passed to handle default settings, these should be in the format of:
                    ('attribute name',default_setting)
                    not all items need to be tuples, you can mix and match strings and tuples for fields with no
                    requirement.

        skip_list: a list of attributes to skip

            .. note::
                * if the attribute '_args_skip_list' exists in the parent object, this will be used.

        skip_startswith: skip attributes that start with this string (defaults to '_')

            .. note::
                * if the attribute '_args_skip_startswith' exists in the parent object, this will be used.

        overwrite: overwrite existing attributes, can be set to False if you do not want to update existing attributes

            .. note::
                * if the attribute '_args_overwrite' exists in the parent object, this will be used.

        do_not_check_parent_attrs: will not check parent attributes for skip parameters.  (used when these fields are
            in use in the parent object for something else)

            .. note::
                * this only happens if the parameter is not passed, otherwise the check is skipped.

        Example of use:

            class MyObject(object):

                def __init__(self, *args, **kwargs):
                    args_handler(self, args, ['f_name', 'l_name'], kwargs)
                    # this would apply the first two args as MyObject.f_name and MyObject.l_name, as well as any kwargs


        Examples of options:

            >>> tc = TmpClass()
    
            test_args = [1, 2, 3, 4]
            test_args_list_1 = ['t1', 't2', 't3', '_t4']
            test_kwargs = {'t5': 5, 't6': 6, 't7': 7, '_t8': 8}
            test_kwargs_ovr = {'t3': 33, '_t4': 44, 't5': 5, 't6': 6, 't7': 7, '_t8': 8}
            test_skip_list = ['t4', 't5']

            test_args_req = [1, 2, 4]
            test_args_list_req = ['t1', '*t2', 't3', '_t4', '*t6']
            test_kwargs_req = {'t5': 5, 't7': 7, '_t8': 8}

            >>> args_handler(tc, test_args, test_args_list_1)
            >>> tc.t2
            2

            >>> args_handler(tc, kwargs=test_kwargs)
            >>> tc.t5
            5

            >>> args_handler(tc, test_args, test_args_list_1, test_kwargs)
            >>> tc.t2
            2
            >>> tc.t5
            5

            >>> args_handler(tc, test_args, test_args_list_1, test_kwargs_ovr)
            >>> tc.t3
            33
            >>> tc.t5
            5
            >>> tc.t2
            2



            >>> args_handler(tc, test_args, test_args_list_1, test_kwargs, skip_list=test_skip_list)
            >>> tc.t2
            2
            >>> tc.t6
            6

            tc.t1 = 11
            >>> args_handler(tc, test_args, test_args_list_1, test_kwargs, skip_list=test_skip_list)
            >>> tc.t1
            1

            >>> tc.t1 = 11
            >>> args_handler(tc, test_args, test_args_list_1, skip_list=test_skip_list, overwrite=False)
            >>> tc.t1
            11


            >>> args_handler(tc, test_args, test_args_list_1, test_kwargs, skip_list=test_skip_list)
            >>> tc.t2
            2
            >>> tc.t6
            6

            >>> tc._args_skip_list = test_skip_list
            >>> args_handler(tc, test_args, test_args_list_1, test_kwargs)
            >>> tc.t2
            2
            >>> tc.t6
            6

            >>> tc._args_skip_list = test_skip_list
            >>> args_handler(tc, kwargs=test_kwargs, do_not_check_parent_attrs=True)
            >>> tc.t5
            5


            >>> test_args = [1, 2, 4]
            >>> test_args_list = [('t1', 11), '*t2', 't3', '_t4', ('t5', 55), ('*t6', 66)]
            >>> test_kwargs = {'t6': 6, 't7': 7, '_t8': 8}
            >>> args_handler(tc, test_args, test_args_list, test_kwargs)

            >>> tc.t1
            1
            >>> tc.t5
            55
            >>> tc.t6
            6

    """

    def _save(save_arg, save_attr, clean_default=True):
        if _check(save_attr):
            setattr(parent_obj, save_attr, save_arg)
            if clean_default:
                try:
                    del attr_defaults[save_attr]
                except KeyError:
                    pass

    def _check(check_attr, check_present=True):
        if check_present:
            if not check_attr.startswith(skip_startswith) and check_attr not in skip_list:
                return overwrite or not hasattr(parent_obj, check_attr)
            return False
        else:
            return check_attr.startswith(skip_startswith) and check_attr not in skip_list

    def _args_list_iterator():
        for tmp_attr, tmp_arg in zip(attr_list, args):
            try:
                if tmp_attr in kwargs:
                    continue
            except TypeError:
                pass
            _save(tmp_arg, tmp_attr)

    def _args_dict_by_attrs():
        for tmp_attr in attr_list:
            try:
                _save(kwargs[tmp_attr], tmp_attr)
            except KeyError:
                pass

    def _args_dict_iterator(args_dict, clean_default=True):
        for tmp_attr, tmp_arg in args_dict.items():
            _save(tmp_arg, tmp_attr, clean_default)

    if not do_not_check_parent_attrs:
        attr_list = getattr(parent_obj, '_attr_list', attr_list)
        skip_list = getattr(parent_obj, '_args_skip_list', skip_list)
        skip_startswith = getattr(parent_obj, '_args_skip_startswith', skip_startswith)
        overwrite = getattr(parent_obj, '_args_overwrite', overwrite)

    if skip_list is None:
        skip_list = []

    attr_defaults = {}

    # ---- verify required fields and build defaults list from tuples ------
    if attr_list:
        if args:
            arg_cnt = len(args)
        else:
            arg_cnt = 0

        tmp_attr_list = []
        for offset, attr in enumerate(attr_list):
            if isinstance(attr, tuple):
                attr_defaults[attr[0]] = attr[1]
                attr = attr[0]
            attr = str(attr)
            if attr[0] == '*':
                attr = attr[1:]

                attr_found = False
                if attr in kwargs:
                    attr_found = True
                if offset <= arg_cnt:
                    attr_found = True

                if not attr_found:
                    raise AttributeError('ArgsHandler: Required attribute ' + attr + ' is not found in args or kwargs')

            tmp_attr_list.append(attr)

        attr_list = tmp_attr_list

    if attr_list is None and args:
        raise AttributeError('ArgsHandler: if args are passed, args list must not be empty')

    if kwargs:
        if attr_list and not args:
            _args_dict_by_attrs()
        else:
            _args_dict_iterator(kwargs)

    if args:
        _args_list_iterator()

    _args_dict_iterator(attr_defaults, clean_default=False)


# ===============================================================================
# Generic Meta Object
# ===============================================================================


class GenericMeta(object):
    """
    Base object to use for creating meta objects.  This will copy all attrs from the meta object to the parent object.

    This can be used to assign lists or other mutatable objects to Classes as well as to create standard sets of metadata
    for classes that can be reused.

    This uses :py:func:`args_handler` to copy kwargs to the class on init.

    Example:

        >>> class MyObject(object):
        >>>     meta = GenericMeta(name='coolObject', number_list=[1,2,3,4])

        >>> mo = MyObject()
        >>> mo.name
        'coolObject'
        >>> mo.number_list
        [1,2,3,4]

    """

    def __init__(self, *kwargs):
        args_handler(self, kwargs=kwargs)

    def get_meta_attrs(self, parent_obj, skip_list=None, skip_startswith='_', overwrite=True):
        """
        Function to copy the atttrs.

        :param parent_obj: The object to copy the attrs TO
        :param skip_list:  A list of attrs to skip copying.
        :param skip_startswith:  If an attr starts with this (default = '_'), do not copy
        :param overwrite: if False (default = True) will not not overwrite existing attributes if they exist.
        """
        if skip_list is None:
            skip_list = []
        for attr, value in iter(self.__dict__.items()):
            if not attr.startswith(skip_startswith) and attr not in skip_list:
                if not hasattr(parent_obj, attr) or overwrite:
                    setattr(parent_obj, attr, value)


def get_meta_attrs(meta, parent_obj, skip_list=None, skip_startswith='_', overwrite=True):
    """
    Standalone version of the get_meta_attrs from the generic meta object for use in other custom classes.

    :param meta: The object to copy the attrs FROM
    :param parent_obj: The object to copy the attrs TO
    :param skip_list:  A list of attrs to skip copying.
    :param skip_startswith:  If an attr starts with this (default = '_'), do not copy
    :param overwrite: if False (default = True) will not not overwrite existing attributes if they exist.
    """
    if skip_list is None:
        skip_list = []
    for attr, value in iter(meta.__dict__.items()):
        if not attr.startswith(skip_startswith) and attr not in skip_list:
            if not hasattr(parent_obj, attr) or overwrite:
                setattr(parent_obj, attr, value)


# ===============================================================================
# Quarter Calc  (not flexible enough to use broadly at this point)
# ===============================================================================

#: TODO make this work for more options

def quarter_calc(*args):
    arg = []
    for a in args:
        arg.append(int(a))

    if len(args) == 1:
        response_item = {}
        if arg[0] % 1 == 0:
            qtr = arg[0] % 4
            yr = 2000 + ( ( arg[0] - qtr ) / 4 )
            qtr += 1
            response_item['year'] = yr
            response_item['quarter'] = qtr
            response_item['word'] = '{year}-Q{quarter}'.format(**response_item)

        return response_item

    elif ( len(args) ) == 2:
        response_item = 0
        if arg[0] > 4:
            yr = arg[0]
            qt = arg[1]
        else:
            yr = arg[1]
            qt = arg[0]

        return ( ( yr - 2000 ) * 4 ) + ( qt - 1 )

    return ""


# ===============================================================================
# Dictionary Helper Objects
# ===============================================================================


class DictKey2Method(object):
    """
    Helper utility to allow dict keys to be accessed by attrs.

    Example:

        >>> d = {'one': 1, 'two': 2}
        >>> dk2m = DictKey2Method(d)
        >>> dk2m.one
        1
        >>> dk2m.two
        2
    """

    def __init__(self, mydict):
        self.mydict = mydict

    def __getattr__(self, item):
        try:
            return self.mydict[item]
        except KeyError:
            raise KeyError(item, ' is not a valid key for this dictionary')

    def __setattr__(self, key, value):
        if key in ('mydict',):
            self.__dict__[key] = value
        else:
            self.mydict[key] = value


class AdvDict(dict):
    """
    A dictionary that allows you to access contents as if they were methods.

    This uses the :py:class:`DictKey2Method` class and wraps it in a :py:class:`dict`.  This also forces the method
    lookups to use a special method name, thus minimizing conflicts with the existing dict methods.

    :param property_name: The name of the property to use to access the fields. (Default = 'key')

    Example:

        >>> d = AdvDict()
        >>> d['one'] = 1
        >>> d['two'] = 2
        >>> d['three'] = 3
        >>> d.key.one
        1

        >>> d = AdvDict(property_name='number')
        >>> d['one'] = 1
        >>> d['two'] = 2
        >>> d['three'] = 3
        >>> d.number.two
        2

    """

    def __init__(self, *args, **kwargs):
        property_name = kwargs.pop('property_name', 'key')
        super(AdvDict, self).__init__(*args, **kwargs)
        setattr(self, property_name, DictKey2Method(self))


# ===============================================================================
# a list that allows for lookups more like a dictionary.
# ===============================================================================


class DBList(object):
    """
    This is a list type object that also allows for lookups like a dictionary based on stored dict keys.

    The only way this works if if dictionaries are stored in the list, each with a key matching the key string.

    NOTE: if there are dupe items (by defined key) in the starting list, only the last one will be kept.

    :param starting_list: A list of dictionaries, each must contain a key matching the "dict_key" field
    :param dict_key: the key used to find the keys for looking up the dictionaries.

    Example:

        >>> dict_list = [{'name':'john','age':21},{'name':'jane','age':22}]
        >>> dl = DBList(dict_list, 'name')
        >>> dl['john']
        {'name':'john','age':21}
        >>> dl['jane']['age']
        22

    """

    internal_dict = {}

    #: TODO Add rest of list and dict functionality

    def __init__(self,
                 starting_list,
                 dict_key):
        for item in starting_list:
            self.internal_dict[item[dict_key]] = item

    def __iter__(self, key):
        return self.internal_dict[key]

    def get_list(self):
        """
        returns a list of the items.
        """
        return self.internal_dict.items()

    def get_dict(self):
        """
        returns the internal dictionary.
        """
        return self.internal_dict


# ===============================================================================
# general list utilities.
# ===============================================================================


def make_list(in_obj):
    """
    Will take in an object, and if it is not already a list or other iterables, it will convert it to one.

    This is helpfull when you dotn know if someone will pass a single string, or a list of strings (since strings
    are iterable you cant just assume)

    This uses the :py:func:`is_iterable` function from this module.

    :param in_obj: list, string, or other iterable.
    :return: a list object.
    """

    if is_iterable(in_obj):
        return in_obj
    else:
        return [in_obj]


def flatten(l, ltypes=(list, tuple), force=None):
    """
    Will flatten lists and tuples to a single level

    .. note:: from: http://rightfootin.blogspot.com/2006/09/more-on-python-flatten.html

    :param l: list or tuple to be flattened
    :param ltypes: the types of items allowed to be flattened, default = (list, tuple)
    :param force: forces return to be of this type.
    :return: single level list or tuple (same as what went in)

    Example:
        >>> l = [1, 2, 3, [4, 5, [6, 7]]]
        >>> flatten(l)
        [1, 2, 3, 4, 5, 6, 7]

    """

    if is_string(l):
        if force is None:
            return []
        elif force == list:
            return [l]
        elif force == tuple:
            return tuple(l, )
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]
        i += 1
    if force is None:
        return ltype(l)
    else:
        return force(l)


def unpack_class_method(class_object_list, method, ret_type=str, args_list=None, kwargs_dict=None):
    """
    This will iterate through a list of objects and pull a value from each one, even if the items are functions.

    :param class_object_list: A list of objects
    :param method: the method to pull from (string)
    :param return_type: what type of data is expected to be returned. this should be a function/class that will convert
        to the type desired.
        for example, the default is str, but int, float are also options.
    :param args_list: if the method is a function, a list of arguments to pass
    :param kwargs_dict: if the method is a function, a dict of keyword arguments to pass.

    """
    if args_list is None:
        args_list = []
    if kwargs_dict is None:
        kwargs_dict = {}

    tmpretset = []
    class_object_list = flatten(class_object_list)
    for obj in class_object_list:
        func = getattr(obj, method, None)
        if callable(func):
            tmpret = ret_type(func(*args_list, **kwargs_dict))
        else:
            tmpret = ret_type(func)
        tmpretset.append(tmpret)
    return tmpretset


def get_same(l1, l2):
    """
    Returns a list with any items that are the same in both lists

    :param l1: list 1
    :param l2: list 2
    :return: a list of items in both "list 1" and "list 2"
    """
    tmp_list = []
    for li in l1:
        if li in l2:
            tmp_list.append(li)
    return tmp_list


def get_not_in(check_for, check_in):
    """
    Returns a list of items that are NOT in another list

    :param check_for: a list of items to check for
    :param check_in: a list to check
    :return: a list of the items in "check_in" that are NOT in "check_for"
    """
    tmp_list = []
    for li in check_for:
        if li not in check_in:
            tmp_list.append(li)
    return tmp_list


def remove_dupes(l1):
    """
    Returns a list with any duplicates removed.
    (while order is maintained, which duplicate is removed is not controllable)
    :param l1:
    :return:
    """
    return list(set(l1))


# ===============================================================================
# checking for the presence (or absence) of lists in other lists
# ===============================================================================


def list_in_list(is_this, in_this):
    """
    Checks to see if ALL of the items in a list are in the other list

    :param is_this: list of items to check for
    :param in_this: list of items to check against
    :return: booleanTrue if all items in is_this are in in_this.

    .. Warning: currently broken!!!

    """
    #: TODO FIX THIS!!
    is_this = make_list(is_this)
    for item in is_this:
        if item in in_this:
            return True
    return False


def list_not_in_list(is_this, not_in_this):
    is_this = make_list(is_this)
    for item in is_this:
        if item in not_in_this:
            return False
    return True


# ===============================================================================
# Utility counts unique values in a list or dict
# ===============================================================================


def count_unique(data_in, dict_key=None, on_key_error='raise'):
    """
    Counts the unique items a list of items, or counts the unique keys in a list of dicts.

    :param data_in: list or tuple of items to be counted
    :param dict_key: if data_in is a list of dict's, this is the key for which item to compare
    :param on_key_error:
        what to do if there is a KeyError when looking up the dict_key:
        * 'raise' = (default) Raises KeyError
        * 'skip' = skips KeyErrors
        * 'count' = counts KeyErrors as 1
    :return: integer

    """

    tmp_list = []

    if not isinstance(data_in, (list, tuple)):
        raise TypeError('count_unique requires a list or tuple, not a ' + type(data_in).__name__)

    if dict_key:
        for item in data_in:
            try:
                tmp_list.append(item[dict_key])
            except KeyError:
                if on_key_error == 'raise':
                    raise KeyError('count_unique: dict key "' + dict_key + '" not found')
                elif on_key_error == 'count':
                    tmp_list.append('__<no_key_item>__')

    else:
        tmp_list = data_in

    return len(set(tmp_list))


# ===============================================================================
# Advanced List Object
# ===============================================================================


class ListPlus(list):
    """
    adds some additional features to the list object.

    =====================    ===========================================================================================
    ListPlus.add             allows insert new records past the existing last record
    ListPlus.update          allows updating records or adding them past the existing last record
    ListPlus[key] = value    same as listPlus.update though uses list key notation
    ListPlus.get             allows for setting a default response instead of generating an error if rec does not exist.
    =====================    ===========================================================================================
    """

    def _update_function(self, curr_obj, new_obj):
        """
        Allows overriding to allow for manipulating or validating updated information if needed'

        this is called anytime something is updated (not for new records though)

        :param curr_obj: this passes the current object in the list
        :param new_obj: this passes the new object
        :return: returns the object to be saved.
        """
        return new_obj

    def add(self, i, x, **kwargs):
        """
        Will add any needed items to a list to add the new item at the indexed spot.

        :param i: list offset to add item to.
            If this is lower than or equal to the size fo the list, the items will be added directly to the end.
            If this is larger than the list length, new items will be added to the list to pad it out long enough
            to reach this length.
        :param x: the new item to add to the list
        :param new_item_default: the default item that will be added as padding if needed.
            this overrides the class setting if present.
        """
        # print( 'l:', l )
        # print( 'i:', i )
        new_item_default = kwargs.get('new_item_default', self.new_item_default)
        if i >= len(self):
            l = len(self)
            mt_items = i - l
            for ni in range(mt_items):
                self.append(new_item_default)
            self.append(x)
        else:
            self.insert(i, x)

    def set_new_item_default(self, new_item_default):
        """
        This sets the default new item object for when blank items must be added
        :param new_item_default: the item that will be used for blank new items.
        """
        self._new_item_default = new_item_default

    @property
    def new_item_default(self):
        try:
            return self._new_item_default
        except AttributeError:
            self.set_new_item_default(None)
            return self._new_item_default

    def update(self, i, x, **kwargs):
        """
        Updates a specific item at a specific offset, if that item does not exist, padding items will
        be added to the list lengthen it.

        :param i: list offset to update.
        :param x: the new item to update in the list
        :param new_items_default: the default item that will be added as padding if needed,
            this overrides the class setting if present
        """
        new_item_default = kwargs.get('new_item_default', self.new_item_default)

        try:
            tmp_value = self._update_function(copy.deepcopy(self[i]), x)
        except (IndexError, TypeError):
            tmp_value = self._update_function(None, x)

        try:
            self[i] = tmp_value
        except IndexError:
            l = len(self)
            mt_items = i - l
            for ni in range(mt_items):
                self.append(new_item_default)
            self.append(tmp_value)

    def get(self, *args):
        i = args[0]
        if len(args) == 1:
            return self[i]
        elif len(args) == 2:
            try:
                return self[i]
            except IndexError:
                return args[1]
        else:
            raise TypeError('ListPlus.get takes at most 2 arguments, ' + str(len(args)) + ' given')

    '''
    def __setitem__(self, i, x):
        if isinstance(i, int):
            self.update(i, x)
        else:
            raise TypeError('ListPlus indices must be integers, not '+type(i).__name__)
    '''

# ===============================================================================
# Lookup Manager
# ===============================================================================

LookupTuple = collections.namedtuple('LookupTuple', ['stored', 'display', 'reference'])


class LookupItem(LookupTuple):
    '''
    def __init__(self, *args, **kwargs):
        super(LookupItem, self).__init__(*args, **kwargs)
        if not self.reference:
            self.reference = copy.deepcopy(self.stored)
        self.reference = slugify(self.reference)
    '''

    def __init__(self, *args):
        self.stored = args[0]
        self.display = args[1]
        try:
            self.reference = args[2]
        except IndexError:
            pass

    def __str__(self):
        return self.stored


class LookupManager(object):
    def __init__(self, lookup_list):
        """
        This handles a list of tuples where you want to have one string for a lookup, which returns a
        different string, and is called by a third thing.

        This takes a list of tuples and

        :param lookup_list:
                lookup list is a list of tuples (stored_value, display_value [, referenced_name] ):
                    stored value = the value that would be stored in the db
                    representative value = the value that is used for display
                    referenced value is the name used in coding (if not present stored_value is used)
        :param case_sensitive:
                determines if lookups are case sensitive or not.

        .. warning:: still needs work

        """
        #: TODO fix this, needs more thought in how it works
        self.stored_dict = {}
        self.display_dict = {}
        self.reference_dict = {}
        self.data_list = []
        self.lookup_list = []
        self.master_dict = {}

        for l in lookup_list:
            tmp_l = LookupItem(*l)

            self.stored_dict[tmp_l.stored] = tmp_l
            self.display_dict[tmp_l.display] = tmp_l
            self.reference_dict[slugify(tmp_l.reference)] = tmp_l
            self.data_list.append(tmp_l)
            self.lookup_list.append((tmp_l.stored, tmp_l.display ))
            self.master_dict[tmp_l.stored] = tmp_l
            self.master_dict[tmp_l.display] = tmp_l
            self.master_dict[slugify(tmp_l.reference)] = tmp_l

    def __iter__(self):
        for i in self.lookup_list:
            yield i

    def __getattr__(self, item):
        return self.reference_dict[item]

    def __getitem__(self, item):
        return self.master_dict[item]

    def get_by_stored(self, item):
        return self.stored_dict[item]

    def get_by_display(self, item):
        return self.display_dict[item]

# ===============================================================================
# Ordered Set
# ===============================================================================


"""
An OrderedSet is a custom MutableSet that remembers its order, so that every
entry has an index that can be looked up.

Based on a recipe originally posted to ActiveState Recipes by Raymond Hettiger,
and released under the MIT license.

Rob Speer's changes are as follows:

    - changed the content from a doubly-linked list to a regular Python list.
      Seriously, who wants O(1) deletes but O(N) lookups by index?
    - add() returns the index of the added item
    - index() just returns the index of an item
    - added a __getstate__ and __setstate__ so it can be pickled
    - added __getitem__
"""

SLICE_ALL = slice(None)


def is_iterable(obj):
    """
    Are we being asked to look up a list of things, instead of a single thing?
    We check for the `__iter__` attribute so that this can cover types that
    don't have to be known by this module, such as NumPy arrays.

    Strings, however, should be considered as atomic values to look up, not
    iterables.

    We don't need to check for the Python 2 `unicode` type, because it doesn't
    have an `__iter__` attribute anyway.
    """
    return hasattr(obj, '__iter__') and not isinstance(obj, str)


class OrderedSet(collections.MutableSet):
    """
    An OrderedSet is a custom MutableSet that remembers its order, so that
    every entry has an index that can be looked up.


    Based on a recipe originally posted to ActiveState Recipes by Raymond Hettiger,
    and released under the MIT license.

    Rob Speer's changes are as follows:

    * changed the content from a doubly-linked list to a regular Python list.
        Seriously, who wants O(1) deletes but O(N) lookups by index?
    * add() returns the index of the added item
    * index() just returns the index of an item
    * added a __getstate__ and __setstate__ so it can be pickled
    * added __getitem__
    """


    def __init__(self, iterable=None):
        self.items = []
        self.map = {}
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        """
        Get the item at a given index.

        If `index` is a slice, you will get back that slice of items. If it's
        the slice [:], exactly the same object is returned. (If you want an
        independent copy of an OrderedSet, use `OrderedSet.copy()`.)

        If `index` is an iterable, you'll get the OrderedSet of items
        corresponding to those indices. This is similar to NumPy's
        "fancy indexing".
        """
        if index == SLICE_ALL:
            return self
        elif hasattr(index, '__index__') or isinstance(index, slice):
            result = self.items[index]
            if isinstance(result, list):
                return OrderedSet(result)
            else:
                return result
        elif is_iterable(index):
            return OrderedSet([self.items[i] for i in index])
        else:
            raise TypeError("Don't know how to index an OrderedSet by %r" %
                            index)

    def copy(self):
        return OrderedSet(self)

    def __getstate__(self):
        if len(self) == 0:
            # The state can't be an empty list.
            # We need to return a truthy value, or else __setstate__ won't be run.
            #
            # This could have been done more gracefully by always putting the state
            # in a tuple, but this way is backwards- and forwards- compatible with
            # previous versions of OrderedSet.
            return (None,)
        else:
            return list(self)

    def __setstate__(self, state):
        if state == (None,):
            self.__init__([])
        else:
            self.__init__(state)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        """
        Add `key` as an item to this OrderedSet, then return its index.

        If `key` is already in the OrderedSet, return the index it already
        had.
        """
        if key not in self.map:
            self.map[key] = len(self.items)
            self.items.append(key)
        return self.map[key]

    append = add

    def index(self, key):
        """
        Get the index of a given entry, raising an IndexError if it's not
        present.

        `key` can be an iterable of entries that is not a string, in which case
        this returns a list of indices.
        """
        if is_iterable(key):
            return [self.index(subkey) for subkey in key]
        return self.map[key]

    def discard(self, key):
        raise NotImplementedError(
            "Cannot remove items from an existing OrderedSet"
        )

    def __iter__(self):
        return iter(self.items)

    def __reversed__(self):
        return reversed(self.items)

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and self.items == other.items
        return set(self) == set(other)


# ===============================================================================
# swap tool
# ===============================================================================


def swap(item, opt1=True, opt2=False):
    """
    This will take an item and swap it for another item.  By default this is True/False, so if True is passed, False
    is returned.  However, any pair of items can be passed and swapped

    This is used to simplify coding when you dotn want to do lots of if **not** that and the variable can be
    permenantly changed, or when you are swapping non-boolean values.

    :param item: the item to swap
    :param opt1: (default = True) option 1
    :param opt2: (default = False) option 2
    :return: the option that is not used.

    Examples:
        >>> swap(True)
        False
        >>> swap(False)
        True
        >>> swap('Blue', 'Blue', 'Red')
        'Red'

    """
    if item == opt1:
        return opt2
    elif item == opt2:
        return opt1
    else:
        raise AttributeError(str(item) + ' not in available options')


# ===============================================================================
# text utils
# ===============================================================================


def replace_between(instring, start_key, end_key, replace, keep_keys=False, offset_count=1, count=9999):
    """
    Replace text between two keys, optionally including the keys themselves.

    :param instring: The string to search
    :param start_key: The starting boundary key
    :param end_key: The ending boundary key
    :param replace: The string to put between the boundary keys
    :param keep_keys: True/False: include the key strings in the replacement
    :param count: replace up to this many instances
    :param offset_count: start replacing after this many instances
    :return: String
    """
    instring = str(instring)

    if start_key not in instring:
        return instring

    start_pos = 0
    curs_pos = 0
    found = 0
    start_key_len = len(start_key)
    end_key_len = len(end_key)
    outstring = ''

    start_pos = index_of_count(instring, find=start_key, offset_count=offset_count, start=0)

    while True:

        if count <= found or start_pos == -1:
            break

        end_pos = instring.find(end_key, start_pos + start_key_len)

        if end_pos == -1:
            break

        if keep_keys:
            suffix = instring[end_pos:end_pos + end_key_len]
            outstring = outstring + instring[curs_pos:start_pos + start_key_len] + replace + suffix
            curs_pos = end_pos + end_key_len

        else:
            outstring = outstring + instring[curs_pos:start_pos] + replace
            curs_pos = end_pos + end_key_len

        found += 1

        start_pos = instring.find(start_key, curs_pos)

    return outstring + instring[curs_pos:]


def index_of_count(instring, find, offset_count=1, start=0):
    """
    Returns the string index (offset) for the x iteration of a substring.

    :param instring: the string to search
    :param find: the string to search for
    :param offset_count: return the 'offset_count' iteration of find string
    :param start: start looking at this point in the string
    :return: the offset for the find string
    :rtype int:

    example:
        >>> index_of_count('abcd abcd abcd abcd','abcd',2)
        6

    """
    if instring:
        offset_loc = start
        current_off = 0
        for i in range(offset_count):
            offset_loc = instring.find(find, current_off)
            if offset_loc > -1:
                if i == offset_count - 1:
                    return offset_loc
                current_off = offset_loc + 1
            else:
                return current_off
        return offset_loc
    return -1


def get_before(instring, find, offset_count=1):
    """
    Returns the string that occurs before the find string. If the find string is not in the string,
    this returns the entire string.

    :param instring: the string to search
    :param find: the string to look for
    :param offset_count: find the nth copy of the find string
    :return: the string that immediatly preceeds the find string.


    example:
        >>> get_before('look for the [key] in the lock','[')
        'look for the '

    """
    if find in instring:
        offset_loc = index_of_count(instring, find, offset_count)

        if offset_loc != -1:
            return instring[:offset_loc]
        return instring
    return instring


def get_after(instring, find, offset_count=1):
    """
    Returns the string that occurs after the find string. If the find string is not in the string,
    this returns the entire string.

    :param instring: the string to search
    :param find: the string to look for
    :param offset_count: find the nth copy of the find string
    :return: the string that is immediatly after the find string.


    example:
        >>> get_after('look for the [key] in the lock',']')
        ' in the lock'

    """
    if find in instring:
        offset_len = len(find)
        offset_loc = index_of_count(instring, find, offset_count)

        if offset_loc != -1:
            return_size = offset_loc + offset_len
            return instring[return_size:]
        return instring
    return instring


def get_between(instring, start_key, end_key):
    """
    Returns the string that occurs between the keys
    :param instring: the string to search
    :param start_key: the string to use to start capturing
    :param end_key: the key to use to end capturing
    :return: the string that is between the start_key and the after_key

    example:
        >>> get_betweem('look for the [key] in the lock','[',']')
        'key'

    """
    return get_after(get_before(instring, end_key), start_key)


# ===============================================================================
# Format number as clean string
# ===============================================================================

import re
from unicodedata import normalize

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify2(text, delim=u'-'):
    """Generates a slightly worse ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    print('sluggify result:', result)
    return str(delim.join(result))


def slugify(text, delim='_', case='lower', allowed=None, punct_replace='', encode=None):
    """
    generates a simpler text string.

    :param text:
    :param delim: a string used to delimit words
    :param case: ['lower'/'upper'/'no_change']
    :param allowed: a string of characters allowed that will not be replaced.  (other than normal alpha-numeric which
        are never replaced.
    :param punct_replace: a string used to replace punction characters, if '', the characters will be deleted.
    :param encode: Will encode the result in this format.
    :return:
    """
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


# ===============================================================================
# Format number as clean string
# ===============================================================================


def format_as_decimal_string(num, max_decimal_points=6):
    """
    This will format a number as a string including decimals, but will correctly trim the decimal.
    :param num: number to format
    :param max_decimal_points: the max decimals to show
    :return: a string of the number with decimals.

    Examples:
        >>> format_as_decimal_string(1.234)
        '1.234'       # this would normally be '1.234000' when done by the normal format

    """
    if isinstance(num, str):
        if num.isnumeric():
            num = Decimal(num)
        else:
            return ''

    if (num % 1 == 0) or (num > 100):
        return '{:,.0f}'.format(num)
    else:
        tmp_dec_pl = '{}'.format(max_decimal_points)
        tmp_format = '{0:.' + tmp_dec_pl + 'g}'
        tmp_num_str = tmp_format.format(num)
        tmp_num_str = tmp_num_str.rstrip('0').rstrip('.')
        return tmp_num_str


# ===============================================================================
# return boolean from varied strings
# ===============================================================================

def convert_to_boolean(obj):
    """
    Converts an object to a boolean, mostly for strings, but can also accept objects that will convert correctly.
    :param obj: the object to convert
    :return: a boolean representing the object

    Examples:
        >>> convert_to_boolean('yes')
        True
        >>> convert_to_boolean(0)
        False

    """
    istrue = ('true', 'yes', 'ok', '1', 'on', '+', 'True', 'Yes', 'Ok', 'On', 'TRUE', 'YES', 'OK', 'ON', 1, 1.0)
    isfalse = ('false', 'no', '0', '-', 'off', 'False', 'No', 'Off', 'FALSE', 'NO', 'OFF', 0, 0.0)

    if isinstance(obj, (str, int, float)):
        if obj in istrue:
            return True
        elif obj in isfalse:
            return False
        else:
            raise TypeError('could not convert to boolean')

    elif hasattr(obj, '__bool__'):
        return bool(obj)

    raise TypeError('could not convert to boolean')


# ===============================================================================
# text / string utils
# ===============================================================================


def is_string(in_obj):
    """ is this a string or not """
    return isinstance(in_obj, str)


def elipse_trim(instr, trim_length, elipse_string='...'):
    """
    Makes sure strings are less than a specified length, and adds an elipse if it needed to trim them.

    :param instr: The String to trim
    :param trim_length: The max length, INCLUDING the elipse
    :param elipse_string: the string used for the elipse.  Default: '...'
    :return: Trimmed string

    Examples:
        >>> elipse_trim('this is a long string',10)
        'this is...'

    """
    instr = str(instr)
    str_len = trim_length - len(elipse_string)
    if len(instr) > trim_length:
        return '{}{}'.format(instr[:str_len], elipse_string)
    else:
        return instr


def concat(*args, separator=' ', trim_items=True):
    """
    Concatenates strings or iterables

    :param args: strings or iterables
    :param separator: the string that will be used between strings.  Default: ' '
    :param trim_items: True/False, trim strings before concatenating.
    :return: string created from contents passed
    """
    # tmp_str = ""

    args = flatten(args)
    tmp_args = []
    for a in args:
        if trim_items:
            tmp_args.append(str(a).strip())
        else:
            tmp_args.append(str(a))
    return separator.join(tmp_args)

    '''
    for arg in args:
        if is_string(arg):
            if trim_items:
                arg = arg.strip()
            tmp_str = tmp_str + separator + str(arg)
            tmp_str = tmp_str.strip()
        else:
            try:
                for x in range(len(arg)):
                    tmp_str = tmp_str + separator + str(arg[x])
                    tmp_str = tmp_str.strip()

            except TypeError:
                tmp_str = str(arg)

    return tmp_str
    '''


# ===============================================================================
# Tree dictionary
# ===============================================================================


class TreeItem():
    _key = ''
    _parent = None
    _children = []
    _item_dict = {}

    def __init__(self,
                 key='',
                 parent=None,
                 children={},
                 item={}):
        self._key = key
        self._parent = parent
        self._children = children
        self._item_dict = item


class TreeDict():
    _root_dict = {}
    _root_node = TreeItem(key='root'
                          )

    def __init__(self,
                 initial_list,
                 key_field='key',
                 parent_key='parent',
                 children_field='children'):
        self._initial_list = initial_list
        self._key_field = key_field
        self._parent_key = parent_key
        self._children_field = children_field

        for item in initial_list:
            self._add_to_tree(item)


    def _search_tree(self, key, dict_tree):
        if key in dict_tree:
            return dict_tree[key]
        else:
            for item in iter(dict_tree.values()):
                if item._children:
                    return self._search_tree(key, item._children)
        return None

    def _add_to_tree(self, node_dict):
        parent_node = None
        if node_dict[self._parent_key]:
            parent_node = self._search_tree(node_dict[self._parent_key], self._root_node._children)

        if not parent_node:
            parent_node = self._root_node

        parent_node._children[node_dict[self._key_field]] = TreeItem(key=node_dict[self._key_field],
                                                                     parent=parent_node,
                                                                     children={},
                                                                     item=node_dict,
                                                                     )

    def add_list(self, list_in):
        for item in list_in:
            self._add_to_tree(item)


    def _get_dnk(self, dict_list):
        tmp_list = []
        for item in iter(dict_list.values()):
            if item._children:
                children_list = self._get_dnk(item._children)
            else:
                children_list = []

            tmp_dict = {}
            tmp_dict.update(item._item_dict)
            tmp_dict[self._children_field] = children_list

            tmp_list.append(tmp_dict)

        return tmp_list

    def get_dict_no_key(self):
        return self._get_dnk(self._root_node._children)
