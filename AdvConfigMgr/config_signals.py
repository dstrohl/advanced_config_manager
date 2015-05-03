__author__ = 'dstrohl'

from .config_logging import get_log
from copy import deepcopy
from .config_exceptions import Error


log = get_log(__name__)

_SIGNAL_PARAMETERS_ = dict(
    pre_write=["storage_manager", "section", "option", "value"],
    post_write=["storage_manager", "section", "option", "value"],
    pre_read=["section", "option", "current_value", "value"],
    post_read=["sectiom", "option", "value"],
    pre_get=["section", "option", "value"],
    post_get=["section", "option", "value"],
    pre_set=["section", "option", "current_value", "value"],
    post_set=["sectiom", "option", "value"],
    pre_create_option=[" section", "options", "value"],
    post_create_option=["section", "option"],
    pre_clear=["section", "option", "curent_value", "default_value", "value"],
    post_clear=["section", "option", "value"],
    pre_delete=["section", "option", "value"],
    post_delete=["section", "option"],
    pre_create_section=[" section", "value"],
    post_create_section=["section"],
    pre_storage_manager_read=["storage_manager", "sections", "override", "value"],
    post_storage_manager_read=["storage_manager", "sections", "sections_read", "options_read"],
    pre_storage_manager_write=["storage_manager", "sections", "override", "value"],
    post_storage_manager_write=["storage_manager", "sections", "sections_written", "options_written"],
)



class NoSignalError(Error):

    def __init__(self, signal_name):
        Error.__init__(self, 'No signals found matching: %s' % signal_name)
        self.signal_name = signal_name
        self.args = (signal_name, )


class SignalTypeManager(object):
    def __init__(self, signal_name, config_manager, signal_manager):
        log.info('Initializign signal type manager: %s', signal_name)
        self._config_manager = config_manager
        self._signal_manager = signal_manager
        self._signals = [BaseSignalHandler(config_manager=config_manager, signal_type_manager=self, priority=0)]
        self._name = signal_name

    def register_signal(self, handler_obj, priority=None):
        if not isinstance(handler_obj, (list, tuple)):
            handler_obj = [handler_obj]

        for h in handler_obj:
            tmp_handler = h(config_manager=self._config_manager, signal_type_manager=self, priority=priority)
            log.info('Registering signal %s for handler %r', self._name, h)
            self._signals.append(tmp_handler)

        self._sort_handlers()
        log.debug('Signal list for handler %s is: %s', self._name, self._signals)

    def _sort_handlers(self):
        self._signals.sort(key=lambda x: x._priority)

    def signal(self, **kwargs):
        if 'value' in kwargs:
            kwargs['value'] = deepcopy(kwargs.get('value'))
            kwargs['initial_value'] = deepcopy(kwargs.get('value'))
            if 'old_value' in kwargs:
                kwargs['old_value'] = deepcopy(kwargs.get('old_value'))

        for s in self._signals:
            kwargs['value'] = s.process_signal(**kwargs)
        return kwargs['value']

    def __call__(self, *args, **kwargs):
        return self.signal(**kwargs)

    def __repr__(self):
        return self._name


class SignalManager(object):

    def __init__(self, config_manager, initial_signals=None):
        log.info('Initializign signal manager')
        self._signal_handlers = {}
        self._config_manager = config_manager
        if initial_signals is not None:
            self.register_signal(initial_signals)

    def register_signal(self, signal_name, handler_obj=None, priority=None):

        if isinstance(signal_name, (list, tuple)):
            if handler_obj is not None or priority is not None:
                raise AttributeError('Multiple signals cannot be added with handlers or priorities')

            for s in signal_name:
                if s not in self._signal_handlers:
                    self._add_type(s)

        else:
            if signal_name not in self._signal_handlers:
                self._add_type(signal_name)

            if handler_obj is not None:
                self._signal_handlers[signal_name].register_signal(handler_obj, priority=priority)

    def _add_type(self, signal_name):
        self._signal_handlers[signal_name] = SignalTypeManager(signal_name=signal_name,
                                                               signal_manager=self,
                                                               config_manager=self._config_manager)

    def __getattr__(self, signal_name):
        try:
            return self._signal_handlers[signal_name]
        except KeyError:
            raise NoSignalError(signal_name)
            

class BaseSignalHandler(object):
    _default_priority = 100

    def __init__(self, config_manager, signal_type_manager, priority=None):
        self._manager = config_manager
        self._priority = priority or self._default_priority
        self._signal_type_manager = signal_type_manager

    def process_signal(self, **kwargs):
        log.a().debug('Base Signal Fired for signal %s', self._signal_type_manager._name)
        log.a().debug('Arguments: %s', kwargs)
        log.debug('Value: %s', kwargs.get('value', None))
        # self._kwargs_to_property(kwargs)
        tmp_ret = self.process(**kwargs)
        log.debug('Signal Return: %s', tmp_ret).s(2)
        return tmp_ret

    def process(self, **kwargs):
        return kwargs.get('value', None)

    def __repr__(self):
        return '%s.%s' % (self._signal_type_manager, self.__class__.__name__)


class Post_Set_AutoSave(BaseSignalHandler):

    def process(self, **kwargs):
        section = kwargs['section']
        option = kwargs['option']



