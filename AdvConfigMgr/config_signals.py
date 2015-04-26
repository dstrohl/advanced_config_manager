__author__ = 'dstrohl'

from .config_logging import get_log
from copy import deepcopy
from .config_exceptions import Error

"""
Expected Signal types

pre_write:
    happens before anythign else in the write process including interpolation
    after validating that the data can be written though
        storage_manager, section, option, value
        returns value

post_write:
    happens after interpolation
        storage_manager, section, option, value
        returns new_value

pre_read:
    happens before anything else in the set process, parameters passed:
    after validations that the data can be read.
        section, option, cur_value, value
        returns changed_new_value


post_read:
    happens after the data is actually saved in the system:
        sectiom, option, new_value
        returns None

pre_get:
    happens before anythign else in the get including interpolation
        section, option, value
        returns value

post_get:
    happens after interpolation
        section, option, value
        returns new_value

pre_set:
    happens before anything else in the set process, parameters passed:
        section, option, cur_value, value
        returns changed_new_value
post_set:
    happens after the data is actually saved in the system:
        sectiom, option, new_value
        returns None

pre_create_option:
    happens before anythign else in the create process,
     section, options, value=kwargs
        returns kwargs


post_create_option:
    happens after the record is created
        section, option
        returns None

todo
pre_create_section:
    happens before anythign else in the create process,
     section, value=kwargs
        returns kwargs

todo
post_create_section:
    happens after the record is created
        section
        returns None

pre_clear:
    happens before record is cleared
        section, option, current_value, default_value, value=True
            returns Bool OK to clear

post_clear:
    happens after a record is cleared (but before it is deleted if keep_if_empty is False)
        section, option
            returns Bool OK to Delete
                (does not force delete)

pre_delete:
    happens before delete validations happen:
        section, option, value=True
            returns bool OK to delete
                (does not override validations)

post_delete:
    happens after item is deleted:
        section, option
            returns None


pre_storage_manager_read:
    happens after the data is read from storage and converted to a dict, but before it is saved.
        storage_manager, sections, override, value=data
            returns data

post storage_manager_read:
    happens after the data is saved to the system
        storage_manager, sections, sections_read, options_read

pre_storage_manager_write:
    happens after the data is read from the system in dict, but before it is written to storage
        storage_manager, sections, override, value=data
            returns data

post storage_manager_write:
    happens after the data is written to storage
        storage_manager, sections, sections_written, options_written


"""

log = get_log(__name__)


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
            kwargs['value'] = s.process(**kwargs)
        return kwargs['value']

    def __call__(self, **kwargs):
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

    def process(self, **kwargs):
        """
        
        :keyword source: 
        :keyword section: 
        :keyword option: 
        :keyword old_value: 
        :keyword initial_value: 
        :keyword value: 
        :return:
        """
        log.a().debug('Base Signal Fired for signal %s', self._signal_type_manager._name)
        log.a().debug('Arguments: %s', kwargs)
        log.debug('Value: %s', kwargs.get('value', None)).s(2)

        return kwargs.get('value', None)

    def __repr__(self):
        return '%s.%s' % (self._signal_type_manager, self.__class__.__name__)

