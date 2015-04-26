__author__ = 'dstrohl'

import unittest
from AdvConfigMgr.config_interpolation import Interpolation
from AdvConfigMgr.config_transform import Xform
# from AdvConfigMgr.config_types import _UNSET
from AdvConfigMgr.utils.base_utils import get_after, get_before

'''
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
                #     tmp_ret += key_sep
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

'''


class quick_ml_dict(object):
    def __init__(self, indict):
        self._data = indict

    def __getitem__(self, item):
        sec = get_before(item, '.')
        opt = get_after(item, '.')

        return self._data[sec][opt]


class InterpolationTest(unittest.TestCase):

    test_map = {
        'fname': 'john',
        'lname': 'buck',
        'zip': '12345',
        'street': 'main st.',
        'city': 'anytown',
        'address': '%(zip) %(street)',
        'fullname': '%(fname) %(lname)',
        'perc': '%%',
        'all': '%(perc) %(fullname) %(address) %% ',
        'spouse': '%(2.fullname)'
    }

    test_map_2 = {
        'fname': 'jane',
        'lname': 'doe',
        'zip': '67890',
        'street': 'broad st.',
        'city': 'anycity',
        'address': '%(zip) %(street)',
        'fullname': '%(fname) %(lname)',
        'perc': '%%',
        'all': '%(perc) %(fullname) %(address) %% ',
        'spouse': '%(1.fullname)'
    }

    test_map_both = quick_ml_dict({'1': test_map, '2': test_map_2})

    def interpolate(self, instr, test_map, current_path=None):
        # md = MultiLevelDictManager(test_map, current_path)
        xf = Xform()
        Inter = Interpolation(test_map, xf)
        return Inter.interpolate(instr, current_path)

    def test_simple_string_return(self):
        test_ret = self.interpolate('name', self.test_map)
        self.assertEqual(test_ret, 'name')

    def test_non_string_return(self):
        test_ret = self.interpolate(123, self.test_map)
        self.assertEqual(test_ret, 123)

    def test_simple_lookup_return(self):
        test_ret = self.interpolate('name: %(fname)', self.test_map)
        self.assertEqual(test_ret, 'name: john')

    def test_2_level_lookup_return(self):
        test_ret = self.interpolate('name: %(1.fname)', self.test_map_both)
        self.assertEqual(test_ret, 'name: john')


    def test_2_level_with_def_path(self):
        test_ret = self.interpolate('name: %(fname)', self.test_map_both, current_path='2')
        self.assertEqual(test_ret, 'name: jane')

    def test_mult_key(self):
        test_ret = self.interpolate('name: %(fname) %(lname)', self.test_map)
        self.assertEqual(test_ret, 'name: john buck')

    def test_recursive_return(self):
        test_ret = self.interpolate('name: %(fullname)', self.test_map)
        self.assertEqual(test_ret, 'name: john buck')

    def test_2_level_recursive_return(self):
        test_ret = self.interpolate('name: %(1.spouse)', self.test_map_both)
        self.assertEqual(test_ret, 'name: jane doe')


