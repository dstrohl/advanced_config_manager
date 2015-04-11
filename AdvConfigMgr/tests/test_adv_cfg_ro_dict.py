__author__ = 'dstrohl'


import unittest
from AdvConfigMgr.config_ro_dict import ConfigDict
from AdvConfigMgr.config_interpolation import Interpolation
from AdvConfigMgr.config_exceptions import NoSectionError, LockedSectionError
from AdvConfigMgr.config_transform import Xform

xf = Xform()


class TestRODict(unittest.TestCase):

    test_dict = {'section1': {'option1': 'opt1', 'option2': 'opt2'},
                 'section2': {'option3': 'opt3', 'option4': '%(option3)'},
                 'section3': {'OpTiOn5': '%(section1.option1)-%(section2.option4)'}}
    c = ConfigDict(test_dict)
    c._interpolator = Interpolation(c, xf)

    def test_build_read(self):
        c = ConfigDict(self.test_dict)
        s2 = c['section2']

        self.assertEqual(c['section1']['option1'], 'opt1')
        self.assertEqual(c['section1.option2'], 'opt2')

        self.assertEqual(s2['option3'], 'opt3')
        self.assertEqual(s2['option4'], '%(option3)')

        self.assertEqual(s2['section3.option5'], '%(section1.option1)-%(section2.option4)')

    def test_interpolation(self):

        c = ConfigDict(self.test_dict)
        c._interpolator = Interpolation(c, xf)
        s2 = c['section2']

        self.assertEqual(s2['option4'], 'opt3')

        self.assertEqual(s2['section3.option5'], 'opt1-opt3')

    def test_len(self):
        self.assertEqual(len(self.c), 3)
        self.assertEqual(len(self.c['section1']), 2)

    def test_raise(self):
        c = ConfigDict(self.test_dict)
        c._raise_on_does_not_exist = True

        with self.assertRaises(NoSectionError):
            tmp_sec = c['junk']

        with self.assertRaises(NoSectionError):
            tmp_sec = c['junk.popsical']

        with self.assertRaises(NoSectionError):
            tmp_sec = c['section1']
            tmp_opt = tmp_sec['junk.more_junk']

        with self.assertRaises(LockedSectionError):
            c['junk.option'] = 'test'

        with self.assertRaises(LockedSectionError):
            del c['junk.option']

    def test_iterate(self):
        i = 0
        for s in self.c:
            i += 1

        self.assertEqual(i, 3)

        i = 0
        for o in self.c['section1']:
            i += 1

        self.assertEqual(i, 2)

    def test_xform(self):
        self.assertEqual(self.c['section1'].name, 'SECTION1')
        self.assertIn('option5', self.c['section3']._options_dict)

    def test_contains(self):
        self.assertIn('section2', self.c)
        self.assertIn('section2.option3', self.c)
        self.assertIn('option3', self.c['section2'])
        self.assertNotIn('section5', self.c)

    def test_set_item(self):
        c = ConfigDict(self.test_dict)
        c._editable = True

        c['section1']['option1'] = 'opt2'
        self.assertEqual(c['section1']['option1'], 'opt2')

        c['section1.option2'] = 'opt3'
        self.assertEqual(c['section1']['option2'], 'opt3')

        c['section1']['section2.option3'] = 'opt33'
        self.assertEqual(c['section2.option3'], 'opt33')

    def test_del_item(self):
        c = ConfigDict(self.test_dict)
        c._editable = True

        del c['section1']['option1']
        self.assertEqual(len(c['section1']), 1)

        s = c['section2']
        del s['option3']
        self.assertEqual(len(c['section2']), 1)

        del c['section1']
        self.assertEqual(len(c), 2)

    def test_str_repr(self):

        self.assertEqual(str(self.c['section1']), 'SECTION1')

        # self.assertEqual(str(self.c['section1'].__repr__), 'SECTION1 Options Dict, 2 options')
        # self.assertEqual(str(self.c.__repr__), 'Read Only Config Dict, 3 sections')
