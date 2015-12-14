__author__ = 'dstrohl'

import unittest
from AdvConfigMgr.data_dict import ConfigDict, _UNSET
from copy import copy, deepcopy

class TestBuildDict(unittest.TestCase):

    def test_build_in_init(self):
        test_dict_in = {
            'section1': {'option1': 'opt1', 'option2': 'opt2'},
            'section2': {'option3': 'opt3', 'option4': '%(option3)'},
            'section3': {'OpTiOn5': '%(.section1.option1)-%(.section2.option4)'},
            'section4': {'option6': 'opt6'}}
        test_dict = ConfigDict(test_dict_in)
                
        self.assertEqual('opt1', test_dict['section1']['option1'])
        self.assertEqual('opt6', test_dict['section4']['option6'])

        with self.assertRaises(AttributeError):
            self.assertEqual('opt1', test_dict.section4['option6'])


    def test_build_in_init_with_depth(self):
        test_dict_in = {
            'section1': {'option1': 'opt1', 'option2': 'opt2'},
            'section2': {'option3': 'opt3', 'option4': '%(option3)'},
            'section3': {'OpTiOn5': '%(.section1.option1)-%(.section2.option4)'},
            'section4': {'option6': 'opt6', 'section5': {'option7': 'opt7'}}}
        test_dict = ConfigDict(test_dict_in, section_depth=1)

        self.assertEqual('opt1', test_dict['section1']['option1'])
        self.assertEqual('opt6', test_dict.section4['option6'])
        with self.assertRaises(AttributeError):
            self.assertEqual('opt6', test_dict.section4.section5['option6'])


    def test_build_after_init(self):
        section1 = ConfigDict({'option1': 'opt1', 'option2': 'opt2'})
        section2 = ConfigDict({'option3': 'opt3', 'option4': '%(option)'})
        section3 = ConfigDict({'OpTiOn5': '%(.section1.option1)-%(.section2.option4)'})
        section4 = ConfigDict({'option6': 'opt6', 'option7': {'option8': 'opt8'}})
        
        test_dict = ConfigDict()
        test_dict['section1'] = section1
        test_dict['section2'] = section2
        test_dict['section3'] = section3
        test_dict['section4'] = section4
        
        self.assertEqual('opt1', test_dict['section1']['option1'])
        self.assertEqual('opt6', test_dict.section4['option6'])

    def test_build_in_init_with_class_in_dict(self):

        section5 = ConfigDict({'option8': 'opt8', 'option9': 'opt9'})
        section1 = ConfigDict({'option1': 'opt1', 'option2': 'opt2'})
        section2 = ConfigDict({'option3': 'opt3', 'option4': '%(option)'})
        section3 = ConfigDict({'OpTiOn5': '%(.section1.option1)-%(.section2.option4)'})
        section4 = ConfigDict({'option6': 'opt6', 'option7': {'option8': 'opt8'}, 'section5': section5})

        test_dict = {
            'section1': section1,
            'section2': section2,
            'section3': section3,
            'section4': section4}
        test_dict = ConfigDict(test_dict)

        self.assertEqual('opt1', test_dict['section1']['option1'])
        self.assertEqual('opt6', test_dict.section4['option6'])
        self.assertEqual('opt9', test_dict.section4.section5['option9'])

    def test_build_in_init_with_regex(self):
        test_dict_in = {
            'section1': {'option1': 'opt1', 'option2': 'opt2'},
            'section2': {'option3': 'opt3', 'option4': '%(option3)'},
            'section3': {'OpTiOn5': '%(.section1.option1)-%(.section2.option4)'},
            'section4': {'option6': 'opt6', 'section5': {'option7': 'opt7'}}}

        test_dict = ConfigDict(test_dict_in, section_regex=r'^section.*$')

        self.assertEqual('opt1', test_dict['section1']['option1'])
        self.assertEqual('opt6', test_dict.section4['option6'])
        self.assertEqual('opt7', test_dict.section4.section5['option7'])

    def test_build_in_init_from_list(self):
        section5 = ConfigDict({'option8': 'opt8', 'option9': 'opt9'}, name='section5')
        section1 = ConfigDict({'option1': 'opt1', 'option2': 'opt2'}, name='section1')
        section2 = ConfigDict({'option3': 'opt3', 'option4': '%(option)'}, name='section2')
        section3 = ConfigDict({'OpTiOn5': '%(.section1.option1)-%(.section2.option4)'}, name='section3')
        section4 = ConfigDict({'option6': 'opt6', 'option7': {'option8': 'opt8'}, 'section5': section5}, name='section4')

        test_dict = ConfigDict(section1, section2, section3, section4)

        self.assertEqual('opt1', test_dict['section1']['option1'])
        self.assertEqual('opt6', test_dict.section4['option6'])
        self.assertEqual('opt8', test_dict.section4.section5['option8'])

    def test_build_with_dot_in_name(self):
        section5 = ConfigDict({'option8': 'opt8', 'option9': 'opt9'}, name='section5')
        section1 = ConfigDict({'option1': 'opt1', 'option2': 'opt2'}, name='section1.section_1')
        section2 = ConfigDict({'option3': 'opt3', 'option4': '%(option)'}, name='section2')
        section3 = ConfigDict({'OpTiOn5': '%(.section1.option1)-%(.section2.option4)'}, name='section3')
        section4 = ConfigDict({'option6': 'opt6', 'option7': {'option8': 'opt8'}, 'section5': section5}, name='section4')

        test_dict = ConfigDict(section1, section2, section3, section4)

        self.assertEqual('opt1', test_dict.section1.section_1['option1'])
        self.assertEqual('opt6', test_dict.section4['option6'])
        self.assertEqual('opt8', test_dict.section4.section5['option8'])


    def test_build_with_dot_in_option_strict(self):
        with self.assertRaises(AttributeError):
            d = ConfigDict(
                {'option1': 'opt1', 'section2.option2': 'opt2'},
                name='section1')

class TestRODict(unittest.TestCase):

    def setUp(self):
        self.section5 = ConfigDict({'option8': 'opt8', 'option9': 'opt9'}, name='section5')
        self.section1 = ConfigDict({'option1': 'opt1', 'option2': 'opt2'}, name='section1')
        self.section2 = ConfigDict({'option3': 'opt3', 'option4': '%(option3)'}, name='section2')
        self.section3 = ConfigDict({'option5': '%(.section1.option1)-%(.section2.option4)'}, name='section3')
        self.section4 = ConfigDict({'option6': 'opt6', 'option7': {'option8': 'opt8'}, 'section5': self.section5}, name='section4')

        self.c = ConfigDict(self.section1, self.section2, self.section3, self.section4)

    def test_navigate(self):

        self.assertEqual('opt3', self.c.section2['option3'])

        s4 = self.c.section4

        self.assertEqual('opt6', s4['option6'])
        self.assertEqual('opt3', s4['.section2.option3'])

        root = s4['..']

        self.assertEqual('opt3', root.section2['option3'])
        self.assertEqual('opt8', s4['section5.option8'])

        s5 = s4['section5']

        self.assertEqual('opt8', s5['option8'])

        root2 = s5['...']

        self.assertEqual('opt3', root.section2['option3'])

        root3 = s5['.']

        self.assertEqual('opt3', root.section2['option3'])

        self.assertEqual('opt3', s5['...section2.option3'])
        self.assertEqual('opt3', s5['.section2.option3'])

    def test_path(self):
        self.assertEqual('.', self.c._path)
        self.assertEqual('.section4', self.c.section4._path)
        self.assertEqual('.section4.section5', self.c.section4.section5._path)



    def test_interpolation(self):

        s2 = self.c['section2']

        self.assertEqual(s2['option4'], 'opt3')

        self.assertEqual(s2['.section3.option5'], 'opt1-opt3')

        self.assertEqual(s2['.section3']._get('option5', raw=True), '%(.section1.option1)-%(.section2.option4)')

    def test_len(self):
        self.assertEqual(len(self.c), 4)
        self.assertEqual(len(self.c['section1']), 2)

    def test_raise(self):

        with self.assertRaises(KeyError):
            tmp_sec = self.c['junk']

        with self.assertRaises(KeyError):
            tmp_sec = self.c['junk.popsical']

        with self.assertRaises(KeyError):
            tmp_sec = self.c.section1['junk.more_junk']

        self.c._lock(recurse=True)

        with self.assertRaises(PermissionError):
            self.c['blah'] = 'foobar'

        with self.assertRaises(PermissionError):
            self.c['blah'] = 'foobar'

        with self.assertRaises(PermissionError):
            del self.c.section1['option1']

        with self.assertRaises(PermissionError):
            del self.c.section1

        self.assertEqual('opt1', self.c.section1['option1'])

    def test_iterate(self):
        i = 0
        names = ['section1', 'section2', 'section3', 'section4']
        for s in self.c:
            self.assertEqual(s._name, names[i])
            i += 1

        self.assertEqual(i, 4)

        i = 0
        for o in self.c['section1']:
            i += 1

        self.assertEqual(i, 2)

    '''
    def test_xform(self):
        self.assertEqual(self.c['section1']._name, 'SECTION1')
        self.assertIn('option5', self.c['section3'])
    '''

    def test_contains(self):
        self.assertIn('section2', self.c)
        self.assertIn('section2.option3', self.c)
        self.assertIn('option3', self.c['section2'])
        self.assertNotIn('section5', self.c)

    def test_set_item(self):
        self.c['section1']['option1'] = 'opt2'
        self.assertEqual(self.c['section1']['option1'], 'opt2')

        self.c['section1.option2'] = 'opt3'
        self.assertEqual(self.c['section1']['option2'], 'opt3')

        self.c['section1']['.section2.option3'] = 'opt33'
        self.assertEqual(self.c['.section2.option3'], 'opt33')

    def test_del_item(self):

        del self.c['section1']['option1']
        self.assertEqual(len(self.c.section1), 1)

        s = self.c['section2']
        del s['option3']
        self.assertEqual(len(self.c['section2']), 1)

        tmp_len = len(self.c)
        del self.c.section1
        self.assertEqual(len(self.c), tmp_len - 1)

    def test_str(self):
        s1 = self.c['section1']
        s_name = str(s1)
        self.assertEqual('section1', s_name)

        self.assertEqual(str(self.c['section1'].__repr__()), 'ConfigDict(.section1) [0 sections, 2 options]')
        self.assertEqual(str(self.c.__repr__()), 'ConfigDict(.) [4 sections, 0 options]')

    def test_update(self):
        self.c._update({'section2.option3': 'opt66'})
        self.assertEqual('opt66', self.c.section2['option3'])

        section7 = ConfigDict({'option10': 'opt10', 'option11': 'opt11'}, name='section7')


        self.c._update(section7)

        self.assertEqual('opt10', self.c.section7['option10'])

        section8 = {'section8': {'option12': 'opt12', 'section9': {'option13': 'opt13'}}}

        self.c._update(section8, section_regex=r'^section.*$')

    def test_compare(self):
        s1 = self.c.section1
        test_compare = s1 == self.section1

        self.assertTrue(test_compare)
    '''
    def test_items_all(self):

        item_cnt = 0
        for s, sec in self.c._items():
            self.assertEqual(self.c[s], sec)
            item_cnt += 1

        self.assertEqual(len(self.c), item_cnt)

    def test_items_options_only(self):
        item_cnt = 0
        for s, sec in self.c._items(options_only=True):
            self.assertTrue(False)
            item_cnt += 1

        self.assertEqual(0, item_cnt)

        item_cnt = 0
        tmp_test = ['opt1', 'opt2']
        for s, sec in self.c.section1._items(options_only=True):
            self.assertEqual(self.c.section1[s], sec)
            item_cnt += 1

        self.assertEqual(0, item_cnt)

    def test_items_sections_only(self):
        item_cnt = 0
        for s, sec in self.c._items(sections_only=True):
            self.assertEqual(self.c[s], sec)
            item_cnt += 1

        self.assertEqual(len(self.c), item_cnt)

        item_cnt = 0
        for s, sec in self.c.section1._items(sections_only=True):
            self.assertFalse(True)
            item_cnt += 1

        self.assertEqual(0, item_cnt)

    def test_values(self):
        item_cnt = 0
        tmp_test = ['opt6', 'opt7', self.section5]
        tmp_ret = self.c.section4._values()

        self.assertListEqual(tmp_test, tmp_ret)

    def test_values_options_only(self):
        item_cnt = 0
        for sec in self.c._values(options_only=True):
            self.assertTrue(False)
            item_cnt += 1

        self.assertEqual(0, item_cnt)

        item_cnt = 0
        tmp_test = ['opt1', 'opt2']
        for sec in self.c.section1._values(options_only=True):
            self.assertEqual(tmp_test[item_cnt], sec)
            item_cnt += 1

        self.assertEqual(0, item_cnt)

    def test_values_sections_only(self):
        item_cnt = 0
        for sec in self.c._values(sections_only=True):
            self.assertEqual(self.c[sec.name], sec)
            item_cnt += 1

        self.assertEqual(len(self.c), item_cnt)

        item_cnt = 0
        for sec in self.c.section1._values(sections_only=True):
            self.assertFalse(True)
            item_cnt += 1

        self.assertEqual(0, item_cnt)
    '''
    def test_keys(self):
        item_cnt = 0
        tmp_test = ['section5', 'option6', 'option7']

        tmp_list = self.c.section4._keys()
        for i in tmp_list:
            self.assertIn(tmp_test.pop(), tmp_list)
        self.assertEqual([], tmp_test)

        # self.assertListEqual(tmp_test, tmp_list)


    def test_clear(self):
        self.c.section1['option1'] = 'opt11'
        self.assertEqual('opt11', self.c.section1['option1'])

        self.c.section1._clear()
        self.assertEqual('opt1', self.c.section1['option1'])

    def test_clear_recurse(self):
        self.c.section1['option1'] = 'opt11'
        self.c.section3['option51'] = 'opt51'
        self.c.section3._set('option52', 'opt52', as_default=True)
        self.c.section3['option52'] = 'opt523'
        self.assertEqual('opt11', self.c.section1['option1'])
        self.assertEqual('opt51', self.c.section3['option51'])
        self.assertEqual('opt523', self.c.section3['option52'])

        self.c._clear(recurse=True)
        self.assertEqual('opt1', self.c.section1['option1'])
        self.assertEqual('opt52', self.c.section3['option52'])

        self.assertEqual(_UNSET, self.c.section3['option51'])

    def test_deepcopy(self):
        self.c.section1['option1'] = 'opt11'
        self.assertEqual('opt11', self.c.section1['option1'])

        tmp_c = deepcopy(self.c)
        self.assertEqual('opt11', tmp_c.section1['option1'])

        self.assertEqual('Root', tmp_c._name)

        tmp_c.section1['option1'] = 'opt13'
        self.assertEqual('opt13', tmp_c.section1['option1'])
        self.assertEqual('opt11', self.c.section1['option1'])

        with self.assertRaises(KeyError):
            tmp_s = tmp_c['..']


    def test_copy(self):
        self.c.section1['option1'] = 'opt11'
        self.assertEqual('opt11', self.c.section1['option1'])

        tmp_s = copy(self.c.section1)
        self.assertEqual('opt11', tmp_s['option1'])

        tmp_s['option1'] = 'opt13'
        self.assertEqual('opt13', tmp_s['option1'])
        self.assertEqual('opt13', self.c.section1['option1'])

        self.assertEqual('Root', tmp_s._name)

        with self.assertRaises(KeyError):
            tmp_c = tmp_s['..']
