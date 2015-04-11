__author__ = 'dstrohl'

import unittest
# from AdvConfigMgr.config_types import Xform, _UNSET


'''
class TestItemKey(unittest.TestCase):

    def test_item_key(self):

        ik = ItemKey('test')
        self.assertEqual(ik.s, 'TEST')
        self.assertEqual(ik.o, 'test')

        ik('sec.opt')
        self.assertEqual(ik.s, 'SEC')
        self.assertEqual(ik.o, 'opt')
        self.assertEqual(ik, 'SEC.opt')

        self.assertEqual(ik(option='opT 2', section=None).s, None)
        self.assertEqual(ik.o, 'opt_2')

        ik2 = ItemKey('sec2.opt3')
        self.assertEqual(ik2.s, 'SEC2')
        self.assertEqual(ik2.o, 'opt3')

        self.assertNotEqual(ik2, ik)

        ik(ik2)
        self.assertEqual(ik.s, 'SEC2')
        self.assertEqual(ik.o, 'opt3')

        self.assertEqual(ik2, ik)

        ik(option='sec4.opt5')
        self.assertEqual(ik.s, 'SEC4')
        self.assertEqual(ik.o, 'opt5')

        ik(section='sec7.opt8')
        self.assertEqual(ik.s, 'SEC7')
        self.assertEqual(ik.o, 'opt8')


        ik(section='sec5', option='sec6.opt7')
        self.assertEqual(ik.s, 'SEC6')
        self.assertEqual(ik.o, 'opt7')

        ik(section='sec5.opt4', option='opt6')
        self.assertEqual(ik.s, 'SEC5')
        self.assertEqual(ik.o, 'opt6')
'''
