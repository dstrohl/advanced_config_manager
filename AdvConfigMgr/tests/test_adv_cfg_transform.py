__author__ = 'dstrohl'

import unittest
from AdvConfigMgr.utils.unset import _UNSET
from AdvConfigMgr.config_transform import Xform

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



