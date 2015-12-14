

from unittest import TestCase

test_str_opt = ConfigOption('t1', data_type='str', cli='-o_str', choices=['t1', 't2', 't2'])
test_int_opt = ConfigOption(100, data_type='int', cli='-o_int')
test_float_opt = ConfigOption(100.1, data_type='float', cli='-o_float')
test_bool_true_opt = ConfigOption(True, data_type='bool', cli='-o_bool')
test_bool_false_opt = ConfigOption(False, data_type='bool', cli='-o_bool')
test_list_opt = ConfigOption(['l1', 'l2'], data_type='list', cli='-o_list')
test_dict_opt = ConfigOption({'d1':'d1'}, data_type='dict')
test_dict_cli_opt = ConfigOption({'d1':'d1'}, data_type='dict', cli='-o_dict')

class TestException(Exception):
    def __init__(self, value):
        self.value = value

def before_change_signal(cfg, path, option, new_value, old_value):
    new_value = old_value+'-'+new_value
    return new_value
    
def after_change_signal(cfg, path, option, new_value):
    if isinstance(cfg.section1['signal_test'], bool):
        return cfg.section1['signal_test']
    else:
        raise TestException(cfg.section1['signal_test'])

def general_signal(cfg):
    if isinstance(cfg.section1['signal_test'], bool):
        return cfg.section1['signal_test']
    else:
        raise TestException(cfg.section1['signal_test'])
        
def storage_signal(cfg, storage):
    if isinstance(cfg.section1['signal_test'], bool):
        return cfg.section1['signal_test']
    else:
        raise TestException(cfg.section1['signal_test'])


class TestBuildConfigManager(TestCase):

    def test_initial_init(self):
        cfg = ConfigManager()

    def test_in_init(self):
        cfg = ConfigManager('section1')

    def test_add_section(self):
        cfg = ConfigManager()
        sec1 = cfg._.add_section('section1')

        self.assertEqual('section1'. sec1._.name)

    def test_add_mult_sections(self):
        cfg = ConfigManager()
        cfg._.add_section('section1', 'section2', 'section3')

        self.assertEqual('section1'. cfg.section1._.name)
        self.assertEqual('section2'. cfg.section2._.name)
        self.assertEqual('section3'. cfg.section3._.name)

    def test_add_section_class(self):
        cfg = ConfigManager(ConfigSection(name='section1'))
        s2 = ConfigSection(name='section2')
        s3 = ConfigSection(name='section3')
        sec1 = cfg._.add_section(s2, s3)

        self.assertEqual('section1'. cfg.section1._.name)
        self.assertEqual('section2'. cfg.section2._.name)
        self.assertEqual('section3'. cfg.section3._.name)


    def test_add_section_dict(self):
        cfg = ConfigManager(dict(name='section1'), dict(name='section1'))
        s3 = dict(name='section3')
        sec1 = cfg._.add_section(s3)

        self.assertEqual('section1'. cfg.section1._.name)
        self.assertEqual('section2'. cfg.section2._.name)
        self.assertEqual('section3'. cfg.section3._.name)

    def test_option_in_section_init(self):
        cfg = ConfigManager()
        s1 = ConfigSection(name='section1', options={'option1':'test1', 'option2':'test2'})
        cfg._.add_section(s1)

        self.assertEqual('test1'. cfg.section1['option1'])
        self.assertEqual('test2'. cfg.section2['option2'])


    def test_option_setitem(self):
        cfg = ConfigManager('section1')
        s1 = cfg.section1

        s1['option1'] = 'test1'

        self.assertEqual('test1', cfg.section1['option1'])


    def test_add_option_class(self):
        cfg = ConfigManager('section1')
        s1 = cfg.section1

        s1['option1'] = ConfigOption('test1')

        self.assertEqual('test1', cfg.section1['option1'])

    def test_add_options_dict(self):
        cfg = ConfigManager('section1')
        s1 = cfg.section1
        s1._.add_option({'option1':'test1', 'option2': 'test2'})

        self.assertEqual('test1', cfg.section1['option1'])
        self.assertEqual('test2', s1['option2'])

    def test_add_options_kwargs(self):
        cfg = ConfigManager('section1')
        s1 = cfg.section1
        s1._.add_option(option1='test1', option2='test2')

        self.assertEqual('test1', cfg.section1['option1'])
        self.assertEqual('test2', s1['option2'])

    def test_options_in_root(self):
        cfg = ConfigManager()

        cfg['option1'] = 'test1'

        self.assertEqual('test1', cfg['option1'])


class TestConfigManagerOps(TestCase):

    def setUp(self):
        self.cfg_dict = ConfigDict()
        self.cfg = ConfigManager(dict_in=self.cfg_dict)
        self.s1 = self.cfg._.add_section(ConfigSection(name='section1', options={'option1':'o1', 'option2':'o2'})

    def test_change_options(self):
        self.assertEqual('o1', self.s1['option1'])
        self.s1['o1'] = 'p1'
        self.assertEqual('p1', self.s1['option1'])

    def test_remove_options(self):
        del self.s1['o1']
        self.assertEqual(1, len(self.s1))

    def test_default_option(self):
        self.cfg._.add_default(ConfigOption(desc='test_desc'))
        self.s1['option3'] = 'o3'

        self.assertEqual('test_desc', self.s1['option1'])
        self.assertEqual('test_desc', self.s1['option2'])
        self.assertEqual('test_desc', self.s1['option3'])


    def test_default_section(self):
        self.cfg._.add_default(ConfigSection(desc='test_desc'))
        self.cfg._.add_section('section2', 'section3')

        self.assertEqual('test_desc', self.s1._.desc)
        self.assertEqual('test_desc', self.s2._.desc)
        self.assertEqual('test_desc', self.s3._.desc)

    
    def test_two_sections_deep(self):
        self.s1._.add_section('section2')
        self.s1.s2['option2-1'] = 'o2.1'

        self.assertEqual('o2.1', self.cfg.s1.s2['option2-1'])

    def test_four_sections_deep(self):
        s2 = ConfigSection('section2', sections='section3')
        self.s1._.add_section(s2)
        self.cfg.section1._.add_section('section3.section4')
        self.cfg.section1_.add_section('.section11.section2')

        self.assertEqual('section1', str(self.cfg.section1))
        self.assertEqual('section2', str(self.cfg_dict.section1.section2))
        self.assertEqual('section3', str(self.cfg.section1.section2.section3))
        self.assertEqual('section4', str(self.cfg_dict.section1.section2.section3.section4))
        self.assertEqual('section11', str(self.cfg.section11))
        self.assertEqual('section2', str(self.cfg_dict.section11.section2))

    def test_clear_option_from_section(self):
        self.assertEqual('o1', self.s1['option1'])
        self.s1['o1'] = 'p1'
        self.assertEqual('p1', self.s1['option1'])
        self.s1._.clear('option1')
        self.assertEqual('o1', self.s1['option1'])

    def test_clear_option_from_option(self):
        self.assertEqual('o1', self.s1['option1'])
        self.s1['o1'] = 'p1'
        self.assertEqual('p1', self.s1['option1'])
        self.s1._['option1'].clear('option1')
        self.assertEqual('o1', self.cfg_dict.section1['option1'])


    def test_clear_section(self):
        self.assertEqual('o1', self.s1['option1'])
        self.assertEqual('o2', self.s1['option2'])

        self.s1['option1'] = 'p1'
        self.s1['option2'] = 'p2'
        self.assertEqual('p1', self.s1['option1'])
        self.assertEqual('p2', self.s1['option2'])
        self.s1._clear(recurse=False)
        self.assertEqual('o1', self.s1['option1'])
        self.assertEqual('o2', self.s1['option2'])

    
    def test_clear_section_recursive(self):
        s2 = self.s1._.add_section('section2')
        s3 = s2._.add_section('section3')
        s2['option2-1'] = 'o2-1'
        s3['option3-1'] = 'o3-1'

        self.s1['option1'] = 'p1'
        s2['option2-1'] = 'p2-1'
        s3['option3-1'] = 'p3-1'

        self.assertEqual('p1', self.s1['option1'])
        self.assertEqual('p2-1', self.s1.section2['option2-1'])
        self.assertEqual('p3-1', self.s1.section2.section3['option3-1'])

        self.cfg._.clear()

        self.assertEqual('o1', self.s1['option1'])
        self.assertEqual('o2-1', self.s1.section2['option2-1'])
        self.assertEqual('o3-1', self.s1.section2.section3['option3-1'])


    def test_update_option_def_values(self):
        s2 = self.s1._.add_section('section2')
        s3 = s2._.add_section('section3')
        s2['option2-1'] = 'o2-1'
        s3['option3-1'] = 'o3-1'

        self.s1._['option1'].set_default('p1')
        self.s1['option2'] = 'p2'
        s2['option2-1'] = 'p2-1'
        s3._['option3-1'].set_default('p3-1')

        self.assertEqual('p1', self.s1['option1'])
        self.assertEqual('p2', self.s1['option2'])
        self.assertEqual('p2-1', self.s1.section2['option2-1'])
        self.assertEqual('p3-1', self.s1.section2.section3['option3-1'])

        self.s1._.clear(recurse=False)

        self.assertEqual('p1', self.s1['option1'])
        self.assertEqual('o2', self.s1['option2'])
        self.assertEqual('p2-1', self.s1.section2['option2-1'])
        self.assertEqual('p3-1', self.s1.section2.section3['option3-1'])

        self.s1._.clear()

        self.assertEqual('p1', self.s1['option1'])
        self.assertEqual('o2', self.s1['option2'])
        self.assertEqual('o2-1', self.s1.section2['option2-1'])
        self.assertEqual('p3-1', self.s1.section2.section3['option3-1'])

    def test_remove_section(self):
        self.assertEqual(2, len(self.cfg))
        del self.cfg.section1
        self.assertEqual(1, len(self.cfg))

    def test_get_dict_recurse(self):
        self.s1._.add_section('section2')
        self.s1.section2['option3'] = 'o3'
        test_dict = self.cfg._.get_dict()

        self.assertIsInstance(test_dict, dict)
        self.assertDictEqual(test_dict, {'section1': {'section2':{'option3':'o3'}, 'option1':'o1', 'option2': 'o2'}})

    def test_get_dict_no_recurse(self):
        self.s1._.add_section('section2')
        self.s1.section2['option3'] = 'o3'
        test_dict = self.s1._.get_dict(recurse=False)

        self.assertIsInstance(test_dict, dict)
        self.assertDictEqual(test_dict, {'option1':'o1', 'option2': 'o2'})

    def test_get_dict_section(self):
        self.s1._.add_section('section2')
        self.s1.section2['option3'] = 'o3'
        test_dict = self.cfg._.get_dict('section1', recurse=False)

        self.assertIsInstance(test_dict, dict)
        self.assertDictEqual(test_dict, {'option1':'o1', 'option2': 'o2'})


class TestValidations(TestCase):

    def setUp(self):
        self.cfg_dict = ConfigDict()
        self.cfg = ConfigManager(dict_in=self.cfg_dict)
        self.s1 = self.cfg._.add_section(ConfigSection(name='section1', options={'option1':'o1', 'option2':'o2'})

    def test_invalid_section(self):
        
        with self.assertRaises(InvalidConfigSectionError):
            junk = self.cfg.foobar
        
    def test_invalid_option(self):
        with self.assertRaises(InvalidConfigOptionError):
            junk = self.cfg.section1['foobar']

    def test_locked_section(self):
        self.s1._.lock()
        with self.assertRaises(LockedConfigSectionError):
            self.cfg.section1['option1'] = 'foobar'

    def test_invalid_type(self):
        with self.assertRaises(InvalidConfigOptionDataTypeError):
            self.cfg.section1['option1'] = dict({'test': 'test'})

        
    def test_option_not_in_choices(self):
        self.s1['option3'] = ConfigOption('t1', choices=['t1','t2','t3'])

        with self.assertRaises(InvalidConfigOptionChoiceError):
            self.cfg.section1['option3'] = 'o2'

    def test_dupe_section(self):
        with self.assertRaises(DuplicateConfigSectionError):
            self.cfg._.add_section('section1')
        
    def test_dupe_option(self):
        with self.assertRaises(DuplicateConfigOptionError):
            self.cfg._.add_option(option1='o1')


class TestDataTypes(TestCase):

    def setUp(self):
        self.cfg_dict = ConfigDict()
        self.cfg = ConfigManager(dict_in=self.cfg_dict)
        self.s1 = self.cfg._.add_section(ConfigSection(name='section1', options={'option1':'o1', 'option2':'o2'})

    def test_int_type(self):
        self.s1['opt1'] = test_int_opt
        self.assertEqual(100, self.s1['opt1'])

        self.s1['opt1'] = 200
        self.assertEqual(200, self.s1['opt1'])

        with self.assertRaises(InvalidConfigOptionDataTypeError):
            self.s1['p[t1'] = 'foobar'

    def test_str_type(self):
        self.s1['opt1'] = test_str_opt
        self.assertEqual('test_str', self.s1['opt1'])

        self.s1['opt1'] = 'test2'
        self.assertEqual('test_str', self.s1['opt1'])

        with self.assertRaises(InvalidConfigOptionDataTypeError):
            self.s1['p[t1'] = 123

    def test_float_type(self):
        self.s1['opt1'] = test_float_opt
        self.assertEqual(100.1, self.s1['opt1'])

        self.s1['opt1'] = 200.2
        self.assertEqual(200.2, self.s1['opt1'])

        with self.assertRaises(InvalidConfigOptionDataTypeError):
            self.s1['p[t1'] = 'foobar'

    def test_bool_true_type(self):
        self.s1['opt1'] = test_bool_true_opt
        self.assertEqual(True, self.s1['opt1'])

        self.s1['opt1'] = False
        self.assertEqual(False, self.s1['opt1'])

        with self.assertRaises(InvalidConfigOptionDataTypeError):
            self.s1['p[t1'] = 123

    def test_bool_false_type(self):
        self.s1['opt1'] = test_bool_false_opt
        self.assertEqual(False, self.s1['opt1'])

        self.s1['opt1'] = True
        self.assertEqual(True, self.s1['opt1'])

        with self.assertRaises(InvalidConfigOptionDataTypeError):
            self.s1['p[t1'] = 123

    def test_list_type(self):
        self.s1['opt1'] = test_list_opt
        self.assertEqual(['l1','l2'], self.s1['opt1'])

        self.s1['opt1'].append('l4')
        self.assertEqual(['l1', 'l2', 'l4'], self.s1['opt1'])

        with self.assertRaises(InvalidConfigOptionDataTypeError):
            self.s1['p[t1'] = 123

    def test_dict_type(self):
        self.s1['opt1'] = test_dict_opt
        self.assertEqual({'d1':'d1'}, self.s1['opt1'])

        self.s1['opt1']['d1'] = 'd3'
        self.assertEqual('d3', self.s1['opt1']['d1'])

        with self.assertRaises(InvalidConfigOptionDataTypeError):
            self.s1['p[t1'] = 123


class TestCLI(TestCase):     

    def setUp(self):
        self.cfg_dict = ConfigDict()
        self.cfg = ConfigManager(dict_in=self.cfg_dict)
        self.s1 = self.cfg._.add_section(ConfigSection(name='section1', options={'option1':'o1', 'option2':'o2'}))


    def test_basic_cli_option(self):
        o1 = ConfigOption('o1', cli=0)
        self.s1._.add_option(option1=o1)

        self.cfg._.parse_cli(['p1'])

        self.assertEqual('p1', self.cfg.section1.option1)

    def test_optional_cli_option(self):
        o1 = ConfigOption('o1', cli='-opt1')
        self.s1._.add_option(option1=o1)

        self.cfg._.parse_cli(['-opt1', 'p1'])

        self.assertEqual('p1', self.cfg.section1.option1)

    def test_optional_cli_option_no_name(self):
        o1 = ConfigOption('o1', cli='-')
        self.s1._.add_option(option1=o1)

        self.cfg._.parse_cli(['-option1', 'p1'])

        self.assertEqual('p1', self.cfg.section1.option1)

    def test_positional_integer_cli(self):
        o1 = ConfigOption(1, cli=10)
        self.s1._.add_option(option1=o1)

        self.cfg._.parse_cli(['3'])

        self.assertEqual(3, self.cfg.section1.option1)

    def test_cli_opts_dict_cli(self):
        o1 = ConfigOption('o1', cli='opt1', cli_args={'default':'p2'})
        self.s1._.add_option(option1=o1)

        self.cfg._.parse_cli([])

        self.assertEqual('p2', self.cfg.section1.option1)
        self.s1._.clear()
        self.assertEqual('o1', self.cfg.section1.option1)

    def test_cli_sec_opts_dict(self):
        s3 = ConfigSection(cli_group='test group')
        o1 = ConfigOption('o1', cli='opt1')
        self.s1._.add_option(option1=o1)

        self.cfg._.parse_cli([])

        self.assertEqual('p2', self.cfg.section1.option1)
        self.s1._.clear()
        self.assertEqual('o1', self.cfg.section1.option1)

    def test_parser_options(self):
        cfg = ConfigParser(cli_parser={'prefix_chars': '+'})

        o1 = ConfigOption('o1', cli='+opt1')
        s1 = cfg._.add_section(ConfigSection('section1', options={'option1': o1}))

        self.cfg._.parse_cli(['+opt1', 'p1'])

        self.assertEqual('p1', self.cfg.section1.option1)


    def test_pass_parser(self):
        parser = argparse.ArgumentParser(prefix_chars='+')
        cfg = ConfigParser(cli_parser=parser)

        o1 = ConfigOption('o1', cli='+opt1')
        s1 = cfg._.add_section(ConfigSection('section1', options={'option1': o1}))

        self.cfg._.parse_cli(['+opt1', 'p1'])

        self.assertEqual('p1', self.cfg.section1.option1)

    def _test_parser_help(self, args_str, expected_help):
        with self.assertRaises(ArgumentParserError) as cm:
            self.cfg._.parse_cli(args_str.split())
        self.assertEqual(expected_help, cm.exception.stdout)

    def test_invalid_cli(self):
        expected_help = '''\
            usage: PROG bar 2 [-h] [-y {1,2,3}] [z [z ...]]

            2 description

            positional arguments:
              z           z help

            optional arguments:
              -h, --help  show this help message and exit
              -y {1,2,3}  y help
            '''
        self._test_parser_help('foo bar', expected_help)

    def test_cli_help(self):
        expected_help = '''\
            usage: PROG bar 2 [-h] [-y {1,2,3}] [z [z ...]]

            2 description

            positional arguments:
              z           z help

            optional arguments:
              -h, --help  show this help message and exit
              -y {1,2,3}  y help
            '''

        o1 = ConfigOption('o1', desc='test_description', help_text='test_help', cli='-')
        self.s1._.add_option(option1=o1)

        tmp_ret = self.cfg._.cli_parser.format_help()

        self.assertEqual(expected_help, tmp_ret)

    def test_cli_usage(self):
        expected_help = '''\
            usage: PROG bar 2 [-h] [-y {1,2,3}] [z [z ...]]

            2 description

            positional arguments:
              z           z help

            optional arguments:
              -h, --help  show this help message and exit
              -y {1,2,3}  y help
            '''

        o1 = ConfigOption('o1', desc='test_description', help_text='test_help', cli='-')
        self.s1._.add_option(option1=o1)

        tmp_ret = self.cfg._.cli_parser.format_usage()

        self.assertEqual(expected_help, tmp_ret)


    def test_return_extra(self):
        o1 = ConfigOption('o1', cli='-')
        self.s1._.add_option(option1=o1)

        tmp_ret = self.cfg._.parse_known_cli(['-option1', 'p1', '-foo', 'bar'])

        self.assertEqual('p1', self.cfg.section1.option1)
        self.assertListEqual(['-foo', 'bar'], tmp_ret)


class TestCLIDataTypes(TestCase):

    def setUp(self):
        self.cfg_dict = ConfigDict()
        self.cfg = ConfigManager(dict_in=self.cfg_dict)
        self.s1 = self.cfg._.add_section(ConfigSection(name='section1', options={'option1':'o1', 'option2':'o2'})

    def _test_parser_help(self, args_str, expected_help):
        with self.assertRaises(ArgumentParserError) as cm:
            self.cfg._.parse_cli()
        return cm.exception.stdout

    def test_int_type(self):
        self.s1['opt1'] = test_int_opt
        expected_help = '''\
            usage: PROG bar 2 [-h] [-y {1,2,3}] [z [z ...]]

            2 description

            positional arguments:
              z           z help

            optional arguments:
              -h, --help  show this help message and exit
              -y {1,2,3}  y help
            '''
        self.cfg._.parse_cli(['o_int', '300'])
        self.assertEqual(300, self.s1['opt1'])

        with self.assertRaises(ArgumentParserError) as cm:
            self.cfg._.parse_cli('o_int', 'test')
        self.assertEqual(expected_help, cm.exception.stdout)

    def test_str_type(self):
        self.s1['opt1'] = test_str_opt
        expected_help = '''\
            usage: PROG bar 2 [-h] [-y {1,2,3}] [z [z ...]]

            2 description

            positional arguments:
              z           z help

            optional arguments:
              -h, --help  show this help message and exit
              -y {1,2,3}  y help
            '''
        self.cfg._.parse_cli(['o_str', 't2'])
        self.assertEqual('t2', self.s1['opt1'])

        with self.assertRaises(ArgumentParserError) as cm:
            self.cfg._.parse_cli(['o_str', 'foobar'])
        self.assertEqual(expected_help, cm.exception.stdout)


    def test_float_type(self):
        self.s1['opt1'] = test_float_opt
        self.assertEqual(100.1, self.s1['opt1'])
        expected_help = '''\
            usage: PROG bar 2 [-h] [-y {1,2,3}] [z [z ...]]

            2 description

            positional arguments:
              z           z help

            optional arguments:
              -h, --help  show this help message and exit
              -y {1,2,3}  y help
            '''
        self.cfg._.parse_cli(['o_float', '300.3'])
        self.assertEqual(300.3, self.s1['opt1'])

        with self.assertRaises(ArgumentParserError) as cm:
            self.cfg._.parse_cli(['o_float', 'foobar'])
        self.assertEqual(expected_help, cm.exception.stdout)

    def test_bool_true_type(self):
        self.s1['opt1'] = test_bool_true_opt
        self.assertEqual(True, self.s1['opt1'])
        expected_help = '''\
            usage: PROG bar 2 [-h] [-y {1,2,3}] [z [z ...]]

            2 description

            positional arguments:
              z           z help

            optional arguments:
              -h, --help  show this help message and exit
              -y {1,2,3}  y help
            '''
        self.cfg._.parse_cli(['-o_true'])
        self.assertEqual(False, self.s1['opt1'])

        self.cfg._.parse_cli([])
        self.assertEqual(True, self.s1['opt1'])

        with self.assertRaises(ArgumentParserError) as cm:
            self.cfg._.parse_cli(['-o_true=test',])
        self.assertEqual(expected_help, cm.exception.stdout)

    def test_bool_false_type(self):
        self.s1['opt1'] = test_bool_false_opt
        self.assertEqual(False, self.s1['opt1'])

        expected_help = '''\
            usage: PROG bar 2 [-h] [-y {1,2,3}] [z [z ...]]

            2 description

            positional arguments:
              z           z help

            optional arguments:
              -h, --help  show this help message and exit
              -y {1,2,3}  y help
            '''
        self.cfg._.parse_cli(['-o_false'])
        self.assertEqual(True, self.s1['opt1'])

        self.cfg._.parse_cli([])
        self.assertEqual(False, self.s1['opt1'])

        with self.assertRaises(ArgumentParserError) as cm:
            self.cfg._.parse_cli(['-o_false=test',])
        self.assertEqual(expected_help, cm.exception.stdout)

    def test_list_type(self):
        self.s1['opt1'] = test_list_opt
        self.assertEqual(['l1','l2'], self.s1['opt1'])

        expected_help = '''\
            usage: PROG bar 2 [-h] [-y {1,2,3}] [z [z ...]]

            2 description

            positional arguments:
              z           z help

            optional arguments:
              -h, --help  show this help message and exit
              -y {1,2,3}  y help
            '''
        self.cfg._.parse_cli(['-o_list','t1', 't2', 't3'])
        self.assertEqual(['t1','t2','t3'], self.s1['opt1'])

        with self.assertRaises(ArgumentParserError) as cm:
            self.cfg._.parse_cli(['-o_list',])
        self.assertEqual(expected_help, cm.exception.stdout)

    def test_dict_type(self):
        with self.assertRaises(ConfigCLIArgumentError):
            self.s1['opt1'] = test_dict_cli_opt



class TestSignals(TestCase):

    def setUp(self):
        self.cfg_dict = ConfigDict()
        self.cfg = ConfigManager(dict_in=self.cfg_dict)
        self.s1 = self.cfg._.add_section(ConfigSection(name='section1', options={'option1':'o1', 'option2':'o2'})

    def test_before_change_signal_option(self):
        self.s1['option1'] = ConfigOption('o1', before_change=before_change_signal)
        self.s1['option1'] = 'o2'
        self.s1['option2'] = 'o3'
        self.assertEqual('o1-o2', self.s1['option1'])
        self.assertEqual('o3', self.s1['option2'])

    def test_after_change_signal_option(self):
        self.s1['option1'] = ConfigOption('o1', after_change=after_change_signal)
        self.s1['signal_test'] = True
        self.s1['option1'] = 'o2'
        self.s1['option2'] = 'o3'
 
        self.assertEqual('o2', self.s1['option1'])
        self.assertEqual('o3', self.s1['option2'])
        
        self.s1['signal_test'] = False
        self.s1['option1'] = 'p2'
        self.s1['option2'] = 'p3'
        self.assertEqual('o2', self.s1['option1'])
        self.assertEqual('p3', self.s1['option2'])
 
        self.s1['signal_test'] = 'Test'
        with self.assertRaises(TestException):
            self.s1['option1'] = 'o2'

    def test_before_change_signal_section(self):
        s2 = self.cfg._.add_section(ConfigSection('section2', before_change=before_change_signal))
        s3 = self.cfg._.add_section('section3')

        s2['option1'] = ConfigOption('o1')
        s2['option2'] = ConfigOption('o3')
        s3['option1'] = ConfigOption('o1')
        s3['option2'] = ConfigOption('o3')

        s2['option1'] = 'o2'
        s2['option2'] = 'o4'        
        s3['option1'] = 'o2'
        s3['option2'] = 'o4'
        
        self.assertEqual('o1-o2', s2['option1'])
        self.assertEqual('o3-o4', s2['option2'])

        self.assertEqual('o2', s3['option1'])
        self.assertEqual('o4', s3['option2'])

    def test_after_change_signal_section(self):
        s2 = self.cfg._.add_section(ConfigSection('section2', after_change=after_change_signal))        
        s3 = self.cfg._.add_section('section3')

        s2['signal_test'] = True
        
        s2['option1'] = ConfigOption('o1')
        s2['option2'] = ConfigOption('o3')
        s3['option1'] = ConfigOption('o1')
        s3['option2'] = ConfigOption('o3')

        s2['option1'] = 'o2'
        s3['option1'] = 'o2'
        self.assertEqual('o2', s2['option1'])
        self.assertEqual('o2', s3['option1'])
        
        s2['signal_test'] = False
        s2['option1'] = 'p2'
        s3['option2'] = 'o4'
        self.assertEqual('o2', s2['option1'])
        self.assertEqual('o4', s3['option2'])

        s2['signal_test'] = 'Test'
        with self.assertRaises(TestException):
            s2['option1'] = 'o2'

    def test_before_change_signal_root(self):
        cfg = ConfigManager(before_change=before_change_signal)
        s2 = cfg._.add_section('section2')
        s3 = cfg._.add_section('section3')

        s2['option1'] = ConfigOption('o1')
        s2['option2'] = ConfigOption('o3')
        s3['option1'] = ConfigOption('o1')
        s3['option2'] = ConfigOption('o3')

        s2['option1'] = 'o2'
        s2['option2'] = 'o4'        
        s3['option1'] = 'o2'
        s3['option2'] = 'o4'
        
        self.assertEqual('o1-o2', s2['option1'])
        self.assertEqual('o3-o4', s2['option2'])

        self.assertEqual('o1-o2', s3['option1'])
        self.assertEqual('o3-o4', s3['option2'])
        

    def test_after_change_signal_root(self):
        cfg = ConfigManager(after_change=after_change_signal)
        s2 = cfg._.add_section('section2')
        s3 = cfg._.add_section('section3')

        s2['signal_test'] = True

        s2['option1'] = ConfigOption('o1')
        s2['option2'] = ConfigOption('o3')
        s3['option1'] = ConfigOption('o1')
        s3['option2'] = ConfigOption('o3')

        s2['option1'] = 'p2'
        s2['option2'] = 'p4'        
        s3['option1'] = 'p2'
        s3['option2'] = 'p4'

        self.assertEqual('p2', s2['option1'])
        self.assertEqual('p4', s2['option2'])
        self.assertEqual('p2', s3['option1'])
        self.assertEqual('p4', s3['option2'])

        s2['signal_test'] = False

        s2['option1'] = 'q2'
        s2['option2'] = 'q4'        
        s3['option1'] = 'q2'
        s3['option2'] = 'q4'

        self.assertEqual('p2', s2['option1'])
        self.assertEqual('p4', s2['option2'])
        self.assertEqual('p2', s3['option1'])
        self.assertEqual('p4', s3['option2'])


        s2['signal_test'] = 'Test'

        with self.assertRaises(TestException):
            s2['option1'] = 'r2'
        with self.assertRaises(TestException):
            s2['option2'] = 'r4'        
        with self.assertRaises(TestException):
            s3['option1'] = 'r2'
        with self.assertRaises(TestException):
            s3['option2'] = 'r4'

        self.assertEqual('p2', s2['option1'])
        self.assertEqual('p4', s2['option2'])
        self.assertEqual('p2', s3['option1'])
        self.assertEqual('p4', s3['option2'])


        
    def test_before_cli_signal_true(self):
        cfg = ConfigManager(before_cli=general_signal)        
        s1 = cfg._.add_section('section1')
        s1['signal_test'] = True
        s1['str_cli'] = test_str_opt
        
        cfg._.parse_cli(['-o_str', 'cli_in'])
        self.assertEqual('cli_in', cfg.section1['option1'])        


    def test_before_cli_signal_false(self):
        cfg = ConfigManager(before_cli=general_signal)        
        s1 = cfg._.add_section('section1')
        s1['signal_test'] = False
        s1['str_cli'] = test_str_opt
        
        cfg._.parse_cli(['-o_str', 'cli_in'])
        self.assertEqual('t1', cfg.section1['option1'])        

    def test_before_cli_signal_other(self):
        cfg = ConfigManager(before_cli=general_signal)        
        s1 = cfg._.add_section('section1')
        s1['signal_test'] = 'other'
        s1['str_cli'] = test_str_opt
        
        with self.assertRaises(TestException):
            cfg._.parse_cli(['-o_str', 'cli_in'])
                
    def test_after_cli_signal_true(self):
        cfg = ConfigManager(after_cli=general_signal)        
        s1 = cfg._.add_section('section1')
        s1['signal_test'] = ConfigOption(True, cli='-t')
        s1['str_cli'] = test_str_opt
        
        cfg._.parse_cli(['-o_str', 'cli_in'])
        self.assertEqual('cli_in', cfg.section1['option1'])        


    def test_after_cli_signal_false(self):
        cfg = ConfigManager(after_cli=general_signal)        
        s1 = cfg._.add_section('section1')
        s1['signal_test'] = ConfigOption(True, cli='-t')
        s1['str_cli'] = test_str_opt
        
        cfg._.parse_cli(['-o_str', 'cli_in', '-t'])
        self.assertEqual('t1', cfg.section1['option1'])        

        


'''
class StorageSignals(TestCase):

    def test_before_load_signal(self):
        
    def test_after_load_signal(self):

    def test_before_storage_load_signal(self):
                
    def test_after_storage_load_signal(self):
        
    def test_before_save_signal(self):
        
    def test_after_save_signal(self):

    def test_before_storage_save_signal(self):
                
    def test_after_storage_save_signal(self):
        
'''

        
class TestMigrations(TestCase):
            
    def test_migrate_data(self):
        
    def test_no_migration(self):
        
        
        
    def test_partial_migration(self):
        
    def test_(self):
        
    
    def test_(self):
        
        
    def test_(self):
        
    def test_(self):
        
        
        
    def test_(self):
        
    def test_(self):