__author__ = 'dstrohl'

import copy
import unittest

from AdvConfigMgr.advconfigmgr import ConfigManager
from AdvConfigMgr.config_validation import ValidationError
from AdvConfigMgr.exceptions.config_exceptions import NoOptionError, NoSectionError, ForbiddenActionError, ip


class TestClass(object):
    t = 'teststring'

    def __str__(self):
        return self.t
'''
class TestDataTypes(unittest.TestCase):

    def setUp(self):
        self.dg = DataTypeGenerator(DataTypeInt, DataTypeStr, DataTypeList, DataTypeFloat, DataTypeDict)

    def test_string(self):
        dt = self.dg('str')()
        # dt = DataTypeStr('test')

        # test to string
        self.assertEqual(dt.to_string('test'), 'test')

        # test from string
        self.assertEqual(dt.from_string('test2'), 'test2')

        # test validations
        with self.assertRaises(ValidationError):
            dt.validated(1)

    def test_int(self):

        validater = ValidateNumRange(1, 100)

        dt = self.dg('int')(validations=validater)

        # test to string
        self.assertEqual(dt.to_string(1), '1')

        # test from string
        dt.from_string('2')
        self.assertEqual(dt.from_string('2'), 2)

        # test validations
        with self.assertRaises(ValidationError):
            dt.validated(101)
            dt.validated('3')

    def test_float(self):
        dt = DataTypeFloat()

        # test to string
        test_str = dt.to_string(1.1)
        self.assertEqual(test_str, '1.1')

        # test from string
        self.assertEqual(dt.from_string('1.2'), 1.2)

        # test with empty
        self.assertEqual(dt.validated(_UNSET), _UNSET)

        # test validations
        with self.assertRaises(ValidationError):
            dt.validated('test')

    def test_list(self):
        dt = DataTypeList(allow_empty=False)

        # test to string
        self.assertEqual(dt.to_string(['test', 'test']), "['test', 'test']")

        # test from string
        self.assertEqual(dt.from_string("['test2', 'test2']"), ['test2', 'test2'])

        # test validations
        with self.assertRaises(ValidationError):
            dt.validated(1)

        with self.assertRaises(ValidationError):
            dt.validated(_UNSET)

    def test_dict(self):
        dt = DataTypeDict()

        # test to string
        self.assertEqual(dt.to_string({'test': 1}), "{'test': 1}")

        # test from string
        self.assertEqual(dt.from_string("{'test': 2}"), {'test': 2})

        # test validations
        with self.assertRaises(ValidationError):
            dt.validated(1)


class TestConfigOption(unittest.TestCase):

    def setUp(self):
        self.cm = ConfigManager()
        self.cs = ConfigSection(self.cm, 'TestSection')
        self.co = ConfigOption(self.cs, 'TestOption')
        self.con = ConfigOption(self.cs, 'TestNumOption', datatype='int')


    def test_set(self):
        self.co.set('testvalue')
        self.assertEqual(self.co.value, 'testvalue')

    def test_is_empty(self):
        self.assertEqual(self.co.is_empty, True)

    def test_can_delete(self):
        self.assertEqual(self.co.can_delete, True)
        self.co.set('testvalue')

    def test_has_default(self):
        self.assertEqual(self.co.has_default_value, False)

    def test_len(self):
        self.co.set('testvalue')
        self.assertEqual(len(self.co), 9)

    def test_validate(self):
        with self.assertRaises(ValidationError):
            self.co.set(1)

    def test_call(self):
        self.assertEqual(self.con(100), 100)

    def test_get_stored_value(self):
        self.con.set(100)
        self.assertEqual(self.con.get_storage_string, '100')

    def test_set_value_from_string(self):
        self.con.set_value_from_string('100')
        self.assertEqual(self.con(), 100)

'''


class NoSectConfigManager(ConfigManager):
    _no_sections = True


class TestConfigManager(unittest.TestCase):

    def setUp(self):
        ip.si(True)
        self.c = ConfigManager()
        self.c.add('section1', 'section2')
        self.od_string1_no_default = {
                     'name': 'od_string1',
                     'verbose_name': 'verbose_od_string1',
                     'description': 'description of od_string1',
                     'keep_if_empty': False}

        self.od_string2_default = {
                     'name': 'od_string2_default',
                     'default_value': 'default_od_string',
                     'keep_if_empty': False}
        self.od_int1_do_not_change = {
                     'name': 'od_int1_do_not_change',
                     'default_value': 1,
                     'do_not_change': True}
        self.od_int2_do_not_delete = {
                     'name': 'od_int2_do_not_delete',
                     'datatype': 'int',
                     'do_not_delete': True}
        self.od_list1_required_after_load = {
                     'name': 'od_list1_required_after_load',
                     'default_value': ['list', 'list']}
        self.od_list2_cli_options = {
                     'name': 'od_list2_cli_options',
                     'default_value': 'list',
                     'cli_option': None}

        self.cli_args_std = {'flags': 'std'}

        self.cli_args_data_true = dict(flags='dt',
                                       data_flag=True)

        self.cli_args_data_true2 = dict(flags='dt2',
                                       data_flag=True)

        self.cli_args_data_false = dict(flags='dtf',
                                       data_flag=False)

        self.cli_args_nargs_2 = dict(flags='nargs',
                                     nargs=2,
                                     default=None)

        self.cli_args_choices = dict(flags='ch',
                                     choices=['ch1', 'ch2'])

        self.cli_args_required = dict(flags='req',
                                      required=True)

        self.cli_args_help = dict(flags='hlp',
                                  help='help_string')


        self.list_of_od = copy.deepcopy([self.od_string1_no_default, self.od_string2_default,
                           self.od_int2_do_not_delete, self.od_int1_do_not_change,
                           self.od_list1_required_after_load, self.od_list2_cli_options])


        self.section_std = {'name': 'section_std',
                            'verbose_name': 'verbose_section_std',
                            'description': 'description of section_std',
                            'options': copy.deepcopy(self.list_of_od)}
        self.section_keep = {'name': 'section_keep',
                             'verbose_name': 'verbose_section_keep',
                             'description': 'description of section_keep'}
        self.section_store_default = {'name': 'section_store_default',
                                      'verbose_name': 'verbose_section_store_default',
                                      'description': 'description of section_store_default',
                                      'storage_read_from_only': 'shared',
                                      'storage_write_to': 'shared',
                                      'store_default': True,
                                      'options': copy.deepcopy(self.list_of_od)}
        self.section_locked = {'name': 'section_locked',
                               'verbose_name': 'verbose_section_locked',
                               'description': 'description of section_locked',
                               'locked': True,
                               'options': copy.deepcopy(self.list_of_od)}
        self.section_disallow_create = {'name': 'section_disallow_create',
                                        'verbose_name': 'verbose_section_disallow_create',
                                        'description': 'description of section_disallow_create',
                                        'allow_create_on_load': False,
                                        'options': copy.deepcopy(self.list_of_od)}

        self.c.add(self.section_std, self.section_disallow_create, self.section_locked,
                   self.section_keep, self.section_store_default)

        self.c['section2'].add('option1',
              self.od_string2_default,
              [self.od_string1_no_default, self.od_int1_do_not_change],
              [('option2', 'opt2'), ('option3', 'opt3')],
              option4=self.od_int2_do_not_delete,
              option5='opt5')

        ip.si(False)
        ip('TEST: Starting test ', self.id()).ms('test').a()

    def tearDown(self):
        ip.mr('test').lp('TEST: Ending test ', self.id())

    def test_add_sections(self):
        # self.c.add(section_std=self.section_std)
        # self.c.add(self.section_keep)
        # self.c.add([self.section_locked, self.section_disallow_create])

        self.assertEqual(len(self.c), 7)
        self.assertEqual(self.c['section1'].name, 'SECTION1')

    def test_add_options(self):
        s = self.c['section2']
        '''
        s.add('option1',
              self.od_string2_default,
              [self.od_string1_no_default, self.od_int1_do_not_change],
              [('option2', 'opt2'), ('option3', 'opt3')],
              option4=self.od_int2_do_not_delete,
              option5='opt5')
        '''
        self.assertEqual(len(s), 8)
        self.assertEqual(s['option2'], 'opt2')

    def test_read_write_options(self):
        s = self.c['section1']
        s.add('option1')
        s['option1'] = 'o1'

        self.assertEqual(s['option1'], 'o1')

    def test_invalid_type(self):
        s = self.c['section1']
        s.add('option1')
        s.option('option1').autoconvert=False
        with self.assertRaises(ValidationError):
            s['option1'] = 1

    def test_invlid_section_option(self):
        with self.assertRaises(NoSectionError):
            s = self.c['no_section']
        with self.assertRaises(NoOptionError):
            s = self.c['section1']['no_option']

    def test_defaults_on_option(self):
        s = self.c['section2']

        self.assertEqual(s['od_string2_default'], 'default_od_string')
        self.assertEqual(self.c['section2']['option2'], 'opt2')
        self.assertEqual(self.c['section2']['option3'], 'opt3')
        self.assertEqual(s['option5'], 'opt5')
        self.assertEqual(s['od_int1_do_not_change'], 1)

    def test_clear_options(self):
        s = self.c['section1']
        s.add('option1', option2='test2')
        s['option1'] = 'test'

        s['option2'] = 'test3'

        self.assertEqual(s['option2'], 'test3')

        s.clear(['option2', 'option1'])

        self.assertEqual(s['option2'], 'test2')
        self.assertEqual(s.item('option1').is_empty, True)

    def test_delete_options(self):
        s = self.c['section1']
        s.add('option1', option2='test2')
        s['option1'] = 'test'

        s['option2'] = 'test3'

        self.assertEqual(s['option2'], 'test3')

        tmp_ret = s.delete(['option2', 'option1'])

        self.assertEqual(tmp_ret, True)

        self.assertIn('option2', s)
        self.assertNotIn('option1', s)

    def test_required_after_load(self):

        opt1 = {'name': 'opt1',
                'datatype': 'int',
                'do_not_delete': True,
                'required_after_load': True}
        opt2 = {'name': 'opt2',
                'default_value': ['list', 'list'],
                'required_after_load': True}

        self.c.add('req_sec')
        self.c['req_sec'].add(opt1, opt2)

        self.assertEqual(self.c.config_ok_after_load, False)
        self.c['req_sec']['opt1'] = 100
        tmp_ret = self.c.config_ok_after_load
        #if not tmp_ret:
        #    ip(self.c.last_fail_list)
        self.assertEqual(tmp_ret, True)

    def test_do_not_change(self):
        self.c._raise_error_on_locked_edit = True
        with self.assertRaises(ForbiddenActionError):
            self.c['section2']['od_int1_do_not_change'] = 100

    def test_keep_if_empty(self):

        s = self.c['section2']
        s['od_string1'] = 'test1'
        s['od_string2_default'] = 'test2'

        s.clear(['od_string1', 'od_string2_default'])

        self.assertIn('od_string2_default', s)
        self.assertNotIn('od_string1', s)

    def test_keep_section_if_empty(self):

        s = self.c['section2']
        s['od_string1'] = 'test1'
        s['od_string2_default'] = 'test2'

        s.clear(['od_string1', 'od_string2_default'])

        self.assertIn('od_string2_default', s)
        self.assertNotIn('od_string1', s)

    def test_cli(self):

        s = self.c['section1']
        item = dict(name='test', cli_options=self.cli_args_std)
        s.add(item)

        self.c.read(storage_names='cli', data=['-std=hello'])

        tmp_resp = s['test']

        self.assertEqual(tmp_resp, 'hello')

    def test_cli_nargs(self):

        s = self.c['section1']
        item = dict(name='test', cli_options=self.cli_args_nargs_2, default_value=[1, 2, 3])
        s.add(item)

        self.assertEqual(s['test'], [1, 2, 3])

        self.c.read(storage_names='cli', data=['-nargs', 'a', 'b'])

        self.assertEqual(s['test'], ['a', 'b'])

    def test_cli_choices(self):

        s = self.c['section1']
        item = dict(name='test', cli_options=self.cli_args_choices, default_value='ch1')
        s.add(item)

        self.assertEqual(s['test'], 'ch1')

        self.c.storage.read(storage_names='cli',data=['-ch=ch2'])

        self.assertEqual(s['test'], 'ch2')

    def test_cli_required(self):

        s = self.c['section1']
        item = dict(name='test', cli_options=self.cli_args_required)
        s.add(item)

        self.c.read(storage_names='cli', data=['-req=ch2'])

        self.assertEqual(s['test'], 'ch2')

    def test_cli_help(self):

        s = self.c['section1']
        item = dict(name='test', cli_options=self.cli_args_help)
        s.add(item)

        self.c.read(storage_names='cli', data=['-hlp=ch2'])

        self.assertEqual(s['test'], 'ch2')

    def test_cli_data_true(self):

        s = self.c['section1']
        item1 = dict(name='test1', cli_options=self.cli_args_data_true, datatype='bool', default_value=False)
        item2 = dict(name='test2', cli_options=self.cli_args_data_false, default_value=True)
        item3 = dict(name='test3', cli_options=self.cli_args_data_true2, default_value='test')

        s.add(item1, item2, item3)

        self.assertEqual(s['test1'], False)
        self.assertEqual(s['test2'], True)
        self.assertEqual(s['test3'], 'test')

        self.c.read(storage_names='cli', data=['-dt', '-dtf'])

        self.assertEqual(s['test1'], True)
        self.assertEqual(s['test2'], False)
        self.assertEqual(s['test3'], 'test')

    def test_simple_config(self):

        #ip.si(False)

        c = NoSectConfigManager()
        c.add(option1='test')

        self.assertEqual(c['option1'], 'test')
        self.assertEqual(len(c), 1)
        self.assertIn('option1', c)

        c['option1'] = 'test2'

        self.assertEqual(c['option1'], 'test2')

    def test_seg_opt_sep(self):
        c = ConfigManager()
        c['section1.option1'] = 'test1'
        c['section1']['option2'] = 'test2'
        self.assertEqual(c['section1']['option1'], 'test1')
        self.assertEqual(c['section1.option2'], 'test2')

        c['section2'] = dict(description='hello world')
        self.assertEqual(c['section2'].description, 'hello world')

        with self.assertRaises(AttributeError):
            c['section3'] = 'testing'

        with self.assertRaises(AttributeError):
            c['section2'] = 'testing'


        self.assertIn('section1.option1', c)
        self.assertNotIn('section1.option4', c)

    def test_debug(self):
        c = ConfigManager()
        c.add('section1')
        c['section1']._debug_()
        c._debug_()


"""
Tests to run:

- setup config
- setup sections
- setup various types
- setup different options
- read options
- change options
- delete options
- check interpolation of options

- check load methods
- check storage methods

"""