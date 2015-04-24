__author__ = 'dstrohl'
__all__ = ['DottedNameString', 'get_log', 'enter', 'leave', 'dns']


from python_log_indenter import IndentedLoggerAdapter
import logging

_DEBUG_ = True

if _DEBUG_:
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

_ROOT_LOG_NAME_ = 'cfg_mgr'


class DottedNameString(object):

    def __init__(self, root='root'):
        self._queue = []
        self._root = root
        self._sep = '.'

    def push(self, name):
        self._queue.append(name)
        return self

    def pop(self, name=None):
        try:
            if name is None:
                self._queue.pop()
            else:
                if name in self._queue:
                    for i in range(len(self._queue)):
                        tmp_name = self._queue.pop()
                        if tmp_name == name:
                            return self
        except IndexError:
            return self

    @property
    def path(self):
        tmp_ret = self._root
        if self._queue:
            tmp_ret += self._sep
            tmp_ret += self._sep.join(self._queue)

        return tmp_ret

    def __str__(self):
        return self.path

    def __len__(self):
        return len(self._queue)+1

    def __repr__(self):
        return self.path

    def __contains__(self, item):
        if item == self._root:
            return True
        else:
            return item in self._queue

    def __call__(self, name=None):
        if name is not None:
            self.push(name)
        return self.path


dns = DottedNameString(root=_ROOT_LOG_NAME_)


def get_log(name):
    """
    :rtype: IndentedLoggerAdapter
    """
    log = IndentedLoggerAdapter(logging.getLogger(name))
    return log


def enter(name=None, level=logging.DEBUG):
    """

    :param name:
    :return:
    :rtype: IndentedLoggerAdapter
    """

    log = get_log(name=dns(name))

    log.log(level, 'Entering process: %s', name).push(dns.path)

    return log


def leave(log, name=None, level=logging.DEBUG):

    if name is None:
        name = str(dns.path)
    else:
        name = dns.pop(name).path

    log.log(level, 'Leaving process: %', name).pop(dns.path)

