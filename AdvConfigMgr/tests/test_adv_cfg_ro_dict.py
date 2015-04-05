__author__ = 'dstrohl'

import unittest
from AdvConfigMgr.advconfigmgr import ConfigRODict
from AdvConfigMgr.config_interpolation import Interpolation

class TestRO_Dict(unittest.TestCase):

    def test_build_read(self):

        test_dict = {'section1': {'option1': 'opt1', 'option2': 'opt2'},
                     'section2': {'option3': 'opt3', 'option4': '%(option3)'},
                     'section3': {'option5': '%(section1.option1)-%(section2.option4)'}}

        c = ConfigRODict(test_dict)
        c._interpolator = Interpolation()
        s2 = c['section2']

        self.assertEqual(c['section1']['option1'], 'opt1')
        self.assertEqual(c['section1.option2'], 'opt2')

        self.assertEqual(s2['option3'], 'opt3')
        self.assertEqual(s2['option4'], 'opt3')

        self.assertEqual(s2['section3.option5'], 'opt1-opt3')



class TesetOptionParsers(unittest.TestCase):

    def setUp(self):
        self.c = ConfigRODict()

    def test_section_option_parser_1(self):
        section, option = self.c._parse_item(section='s', option='o')
        self.assertEqual(section, 's')
        self.assertEqual(option, 'o')

    def test_section_option_parser_2(self):
        section, option = self.c._parse_item(section='s.o')
        self.assertEqual(section, 's')
        self.assertEqual(option, 'o')

    def test_section_option_parser_3(self):
        section, option = self.c._parse_item(option='s.o')
        self.assertEqual(section, 's')
        self.assertEqual(option, 'o')

    def test_section_option_parser_4(self):
        section, option = self.c._parse_item(option='o')
        self.assertEqual(section, None)
        self.assertEqual(option, 'o')

    def test_section_option_parser_5(self):
        section, option = self.c._parse_item(section='s')
        self.assertEqual(section, 's')
        self.assertEqual(option, None)

    def test_section_option_parser_6(self):
        section, option = self.c._parse_item(section='s', option='p.q')
        self.assertEqual(section, 'p')
        self.assertEqual(option, 'q')

