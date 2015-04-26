__author__ = 'dstrohl'

import unittest
from AdvConfigMgr.config_signals import SignalManager, BaseSignalHandler, NoSignalError


class TestSignalTimes2(BaseSignalHandler):
    _default_priority = 20

    def process(self, **kwargs):
        value = kwargs.get('value')
        value *= 2
        return value


class TestSignalPlus100(BaseSignalHandler):
    _default_priority = 100

    def process(self, **kwargs):
        value = kwargs.get('value')
        value += 100
        return value


class TestSignals(unittest.TestCase):

    def test_signals(self):
        sm = SignalManager(self)
        sm.register_signal('test_signal1', (TestSignalPlus100, TestSignalTimes2))
        tmp_ret = sm.test_signal1(value=1)
        self.assertEqual(tmp_ret, 102)

    def test_signal_order2(self):
        sm = SignalManager(self)
        sm.register_signal('test_signal1', TestSignalPlus100, 1)
        sm.register_signal('test_signal1', TestSignalTimes2, 2)
        tmp_ret = sm.test_signal1(value=1)
        self.assertEqual(tmp_ret, 202)

    def test_signal_multi_signals(self):
        sm = SignalManager(self)
        sm.register_signal('test_signal_1', TestSignalPlus100)
        sm.register_signal('test_signal_2', TestSignalTimes2)
        tmp_ret = sm.test_signal_1(value=1)
        tmp_ret2 = sm.test_signal_2(value=2)
        self.assertEqual(tmp_ret, 101)
        self.assertEqual(tmp_ret2, 4)

    def test_signal_raise_exception(self):
        sm = SignalManager(self)
        sm.register_signal('test_signal_1', TestSignalPlus100)

        with self.assertRaises(NoSignalError):

            sm.test_signal_2(value=2)

    def test_signal_default_signal(self):
        sm = SignalManager(self)
        sm.register_signal(('test_signal', 'test2', 'test3'))

        self.assertEqual(sm.test_signal(value=2), 2)
        self.assertEqual(sm.test2(value=2), 2)
        self.assertEqual(sm.test3(value=2), 2)
