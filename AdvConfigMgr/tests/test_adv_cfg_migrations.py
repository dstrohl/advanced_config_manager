__author__ = 'dstrohl'

import unittest

from AdvConfigMgr.advconfigmgr import ConfigManager
from AdvConfigMgr.config_storage import *
from AdvConfigMgr.config_exceptions import NoOptionError

class TestMigrations(unittest.TestCase):

    def run_migrate(self, stored_data, live_data, migration_list):
        c = ConfigManager(migrations=migration_list,
                          storage_managers=ConfigSimpleDictStorage,
                          default_storage_managers='dict')
        c.add_section('section1', version='1.0', options=live_data)
        c.read(data=stored_data)
        return c

    def test_pass(self):

        test_migration_data = {'section1': {'option1': 'test', 'SECTION1_version_number': '0.1'}}

        test_migration_list = [{'section_name': 'section1',
                                'stored_version': '0.1',
                                'live_version': '1.0',
                                'actions': [('pass', 'option1')]}]

        test_live_data = [{'name': 'option1',
                           'default_value': 'oldval'}]

        c = self.run_migrate(test_migration_data, test_live_data, test_migration_list)

        self.assertEqual(c['section1']['option1'], 'test')

    def test_interpolate(self):
        test_migration_data = {'section1': {'option1': 'test', 'SECTION1_version_number': '0.1'}}

        test_migration_list = [{'section_name': 'section1',
                                'stored_version': '0.1',
                                'live_version': '1.0',
                                'actions': [('interpolate', 'option1', 'new_val')]}]

        test_live_data = [{'name': 'option1',
                           'default_value': 'oldval'}]

        c = self.run_migrate(test_migration_data, test_live_data, test_migration_list)

        self.assertEqual(c['section1']['option1'], 'new_val')

    def test_remove(self):
        test_migration_data = {'section1': {'option1': 'test', 'SECTION1_version_number': '0.1'}}

        test_migration_list = [{'section_name': 'section1',
                                'stored_version': '0.1',
                                'live_version': '1.0',
                                'actions': [('remove', 'option1')]}]

        test_live_data = [{'name': 'option2',
                           'default_value': 'oldval'}]

        c = self.run_migrate(test_migration_data, test_live_data, test_migration_list)

        with self.assertRaises(NoOptionError):
            tmp_junk = c['section1']['option1']

    def test_rename(self):
        test_migration_data = {'section1': {'option1': 'test', 'SECTION1_version_number': '0.1'}}

        test_migration_list = [{'section_name': 'section1',
                                'stored_version': '0.1',
                                'live_version': '1.0',
                                'actions': [('rename', 'option1', 'option2')]}]

        test_live_data = [{'name': 'option2',
                           'default_value': 'oldval'}]

        c = self.run_migrate(test_migration_data, test_live_data, test_migration_list)

        self.assertEqual(c['section1']['option2'], 'test')

        with self.assertRaises(NoOptionError):
            tmp_junk = c['section1']['option1']

    def test_copy(self):
        test_stored_data = {'section1': {'option1': 'test', 'SECTION1_version_number': '0.1'}}

        test_migration_list = [{'section_name': 'section1',
                                'stored_version': '0.1',
                                'live_version': '1.0',
                                'actions': [('copy', 'option1', 'option2')]}]

        test_live_data = [{'name': 'option1',
                           'default_value': 'oldval'}]

        c = self.run_migrate(test_stored_data, test_live_data, test_migration_list)

        self.assertEqual(c['section1']['option1'], 'test')
        self.assertEqual(c['section1']['option2'], 'test')

    def test_no_migrate_versions_match(self):
        test_migration_data = {'section1': {'option1': 'test', 'SECTION1_version_number': '1.0'}}

        test_migration_list = [{'section_name': 'section1',
                                'stored_version': '0.1',
                                'live_version': '1.0',
                                'actions': [('interpolate', 'option1', 'new_val')]}]

        test_live_data = [{'name': 'option1',
                           'default_value': 'oldval'}]

        c = self.run_migrate(test_migration_data, test_live_data, test_migration_list)

        self.assertEqual(c['section1']['option1'], 'test')

    def test_no_migrate_storage_mismatch(self):
        test_migration_data = {'section1': {'option1': 'test', 'SECTION1_version_number': '0.1'}}

        test_migration_list = [{'section_name': 'section1',
                                'stored_version_min': '0.2',
                                'stored_version': '0.2',
                                'live_version': '1.0',
                                'actions': [('interpolate', 'option1', 'new_val')]}]

        test_live_data = [{'name': 'option1',
                           'default_value': 'oldval'}]

        c = self.run_migrate(test_migration_data, test_live_data, test_migration_list)

        self.assertEqual(c['section1']['option1'], 'test')
