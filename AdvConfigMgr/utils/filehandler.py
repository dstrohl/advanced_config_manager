__author__ = 'dstrohl'



class FileHandler(object):
    """
    manages a list of open files, this will:
    * accept a filename and return a file handle if it is already open, otherwise opens it and returns it,
    * changes the mode of files if needed
    * allows for close all
    * allows setting of default options, encoding, etc.
    """
    def __init__(self,
                 keep_files_open=False,
                 default_encoding=None,
                 default_mode='r',
                 default_errors=None):

        self._default_encoding = default_encoding
        self._default_mode = default_mode
        self._default_errors = default_errors
        self._keep_files_open = keep_files_open
        self._files = {}

    def register_file(self, filename=None, handle=None, encoding=None, mode='r', errors=None):

        if filename is None and handle is None:
            raise AttributeError('either filename or handle must be passed')

        if filename is None:
            filename = handle.name
            encoding = handle.encoding
            mode = handle.mode
            errors = handle.errors



        tmp_rec = dict(filename=filename, full_path=None, handle=handle, encoding=encoding, mode=mode, errors=errors)
        self._files[tmp_rec]


