__author__ = 'dstrohl'

import unittest
from pathlib import Path

from AdvConfigMgr.advconfigmgr import ConfigManager
from AdvConfigMgr.config_exceptions import ip
from AdvConfigMgr.storage_managers.config_storage import *
from AdvConfigMgr.storage_managers.storage_mongodb import *

from AdvConfigMgr.storage_managers.tests.credentials import *

class TestClass(object):
    t = 'teststring'

    def __str__(self):
        return self.t

class MongoCfgManager(ConfigManager):
    _DEFAULT_STORAGE_PLUGINS = (MongoStorageManager, ConfigCLIStorage)


class TestStorageManagers(unittest.TestCase):
    '''
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

        ip('TEST: Starting test ', self.id()).ms('test').a()



    '''

    @classmethod
    def setUpClass(cls):
        cls.tmp_ini_path = Path(__file__).parent

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.c = ConfigManager()
        self.c.add('section1', 'section2')

        ip('TEST: Starting test ', self.id()).ms('test').a()

    def tearDown(self):
        ip.mr('test').lp('TEST: Ending test ', self.id())

    def test_save_file(self):

        storage_config = {'mongo': {'connection': MONGO_DB_CONNECTION}}
        c = MongoCfgManager(default_storage_managers='mongo', storage_config=storage_config)
        d = MongoCfgManager(default_storage_managers='mongo', storage_config=storage_config)

        c.add_section('Section1')

        c['section1']['option1'] = 'test'

        c.write()

        d.add_section('Section1')

        d['section1']['option1'] = 'nothing'

        d.read()

        self.assertEqual(d['section1']['option1'], 'test')
