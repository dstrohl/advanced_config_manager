__author__ = 'dstrohl'

import unittest

from AdvConfigMgr.data_dict.config_transform import *
from AdvConfigMgr.utils.unset import _UNSET

'''
class TestXform(unittest.TestCase):
    def test_xform(self):
        xf = Xform()

        self.assertEqual(xf.section('sec'), 'SEC')
        self.assertEqual(xf.section('sec.opt'), 'SEC')
        self.assertEqual(xf.option(), 'opt')
        self.assertEqual(xf.section('seE c'), 'SEE_C')
        self.assertEqual(xf.option(), _UNSET)
        self.assertEqual(xf.section('sec_1'), 'SEC_1')
        self.assertEqual(xf.section('s@#c_1'), 'S__C_1')
        self.assertEqual(xf.section('s**1'), 'S__1')
        self.assertEqual(xf.section('h\tell\no'), 'H_ELL_O')
        self.assertEqual(xf.section('hi! there.'), 'HI__THERE')
        self.assertEqual(xf.section('se*[!1[', glob=True), 'SE*[!1[')
        self.assertEqual(xf.section(None), None)

        self.assertEqual(xf.option('opt'), 'opt')
        self.assertEqual(xf.option('sec.opt'), 'opt')
        self.assertEqual(xf.section(), 'SEC')
        self.assertEqual(xf.option('seE c'), 'see_c')
        self.assertEqual(xf.section(), _UNSET)
        self.assertEqual(xf.option('sec_1'), 'sec_1')
        self.assertEqual(xf.option('se*[!1[', glob=True), 'se*[!1[')
        self.assertEqual(xf.option(None), None)

        tmp_check, tmp_ret = xf.full_check('sec.opt')
        self.assertTrue(tmp_check)
        self.assertEqual(tmp_ret, 'SEC.opt')

        tmp_check, tmp_ret = xf.full_check('sec')
        self.assertFalse(tmp_check)
        self.assertEqual(tmp_ret, 'sec')

        tmp_check, tmp_ret = xf.full_check('opt', option_or_section='option')
        self.assertFalse(tmp_check)
        self.assertEqual(tmp_ret, 'opt')

        tmp_check, tmp_ret = xf.full_check('opt', option_or_section='section')
        self.assertFalse(tmp_check)
        self.assertEqual(tmp_ret, 'OPT')

        tmp_check, tmp_ret = xf.full_check('opt2', section='sec2')
        self.assertFalse(tmp_check)
        self.assertEqual(tmp_ret, 'SEC2.opt2')

        tmp_check, tmp_ret = xf.full_check('sec4.opt4', section='sec3')
        self.assertTrue(tmp_check)
        self.assertEqual(tmp_ret, 'SEC4.opt4')
        self.assertEqual(xf.section(), 'SEC4')


        tmp_check, tmp_ret = xf.full_check('sec5', option_or_section='section', option='opt5')
        self.assertFalse(tmp_check)
        self.assertEqual(tmp_ret, 'SEC5.opt5')

'''

class TestInterpolate(unittest.TestCase):

    section = dict(
        test1='this is',
        test2='a test',
        test3='%{test2}',
        test4='%{test1} %{test2}',
        test5='%{test4}, %{test1} another test',
        test6='%{no end bracket',
        test7='%{test6}',
        test8='%{test8}'
    )

    def test_no_interpolation(self):
        self.assertEqual('hello world', interpolate('hello world', section=self.section))

    def test_one_interp(self):
        self.assertEqual('this is foobar', interpolate('%{test1} foobar', section=self.section))

    def test_two_interp(self):
        self.assertEqual('a test is foobar', interpolate('%{test3} is foobar', section=self.section))

    def test_two_deep_interp(self):
        self.assertEqual('this is a test that is foobar', interpolate('%{test4} that is foobar', section=self.section))

    def test_three_deep_interp(self):
        self.assertEqual('this is a test, this is another test that is foobar', interpolate('%{test5} that is foobar', section=self.section))

    def test_raises(self):
        with self.assertRaises(InterpolationDepthError):
            junk = interpolate('%{test8}', section=self.section)

        with self.assertRaises(InterpolationSyntaxError):
            junk = interpolate('%{test6}', section=self.section)

        with self.assertRaises(InterpolationSyntaxError):
            junk = interpolate('%{test7}', section=self.section)

        with self.assertRaises(KeyError):
            junk = interpolate('%{no test}', section=self.section)

