__author__ = 'dstrohl'

from pathlib import Path

__all__ = ['PathHandler', ]


class PathHandler(object):
    """

    This class can help with handling a group of files that come in various formats.

    """


    def __init__(self, *files,
                 glob_sort_order='alpha',
                 glob_sort_dir='asc',
                 return_type='name',
                 force_return=False,
                 verify='call',
                 on_does_not_exist='raise',
                 default_open_mode='rw',
                 default_open_encoding=None):
        """
        :param str sort_order: 'alpha', 'm_date', 'c_date', or 'size'
        :param str sort_dir: 'asc', 'dec'
        :param str return_type: 'name', 'path', 'handle'.  if a file handle is passed in the beginning, it will always be
            returned unless force_return is True.
        :param bool force_return_type: if True, will force the return of a name or path even if a file handle is passed.
        :param str verify: 'call', 'add', 'both', or 'none', verify this file exists when called, when added, or
            do not verify
        :param str on_does_not_exist: 'raise', 'ignore' if a file does not exist, will raise a FileDoesNotExist,
            or ignore it.

        if file does not exist and ignore is set, a list of failed files can be called from
        PathHandler.last_failed_paths.
        """
        self._last_failed_paths = []
        self._last_failed_filenames = []
        self._file_list = []
        self._sort_order = glob_sort_order.lower()
        self._return_type = return_type.lower()
        self._force_return = force_return
        self._verify = verify.lower()
        self._raise_on_does_not_exist = on_does_not_exist.lower() == 'raise'
        self._default_open_mode = default_open_mode
        self._default_open_encoding = default_open_encoding

        if glob_sort_dir == 'asc':
            self._sort_dir = False
        else:
            self._sort_dir = True

        if files:
            self.append(files)

    @property
    def last_failed_paths(self):
        tmp_ret = list(self._last_failed_paths)
        self._last_failed_paths = []
        self._last_failed_filenames = []
        return tmp_ret

    def set_open_mode(self, mode):
        self._default_open_mode = mode

    def _verify(self, action, path):
        if self._verify == 'none':
            return True

        tmp_ret = True

        if self._verify == action or self._verify == 'both':

            if not isinstance(path, Path):
                tmp_ret = path.readable() or path.writable()
            else:
                tmp_ret = path.is_file()

        if not tmp_ret:
            if self._raise_on_does_not_exist:
                raise FileNotFoundError()
            else:
                if str(path) not in self._last_failed_filenames:
                    self._last_failed_paths.append(path)
                    self._last_failed_filenames.append(str(path))

    def append(self, file):
        if file is not None:
            if not isinstance(file, (list, tuple)):
                file = [file]
            for f in file:
                self._file_list.extend(self._parse_for_glob(f))

    def _make_item_dict(self, path):
        tmp_dict = dict(name=path)
        if self._sort_order == 'm_date':
            tmp_dict['sort'] = path.stat().st_mtime()
        elif self._sort_order == 'c_date':
            tmp_dict['sort'] = path.stat().st_ctime()
        elif self._sort_order == 'size':
            tmp_dict['sort'] = path.stat().st_size()
        else:
            tmp_dict['sort'] = str(path.name)

        return tmp_dict

    def _parse_for_glob(self, glob):

        if not isinstance(glob, str):
            return glob

        if "*" in glob or "?" in glob or "[" in glob:
            tmp_file_list = []
            tmp_list = []
            if self._sort_order == 'alpha':
                tmp_list = sorted(Path('.').glob(glob), reverse=self._sort_dir)
            else:
                for file in list(Path('.').glob(glob)):
                    tmp_list.append(self._make_item_dict(file))
                tmp_list = sorted(tmp_list, reverse=self._sort_dir)

            for file in tmp_list:
                if self._verify(file):
                    tmp_file_list.append(file)

            return tmp_file_list
        else:
            return [glob]

    def _force_open_mode(self, file, force_readable=False, force_writable=False, force_mode=None, encoding=None):

        if encoding is None:
            encoding = self._default_open_encoding

        if force_mode is None:
            if force_readable and force_writable:
                mode = 'rw'
            elif force_readable:
                mode = 'r'
            elif force_writable:
                mode = 'w'
            else:
                mode = self._default_open_mode
        else:
            mode = force_mode

        if isinstance(file, Path):
            return file.open(mode=mode, encoding=encoding)

        if isinstance(file, str):
            return Path(file).open(mode=mode, encoding=encoding)

        if force_mode is not None:
            if file.mode() == mode:
                return file
        else:
            if force_readable and force_writable:
                if file.readable() and file.writable():
                    return file

            if force_writable and file.writable():
                return file

            if force_readable and file.readable():
                return file

        tmp_file = file.name
        file.close()
        return open(tmp_file, mode=mode, encoding=self._default_open_encoding)

    def _get_correct_type(self, path, ret_type=None, force_readable=False, force_writable=False, force_mode=None,
                          encoding=None):

        if ret_type is None:
            ret_type = self._return_type

        if isinstance(path, Path):
            if ret_type == 'name':
                return str(path)
            if ret_type == 'handle':
                return self._force_open_mode(path, force_readable, force_writable, force_mode, encoding)
            else:
                return path
        else:
            if self._force_return:
                if ret_type == 'name':
                    return path.name()
                if ret_type == 'path':
                    return Path(path.name)

            return self._force_open_mode(path, force_readable, force_writable, force_mode, encoding)

    @property
    def writable(self):
        for f in self._file_list:
            yield self._get_correct_type(f, force_writable=True)

    @property
    def readable(self):
        for f in self._file_list:
            yield self._get_correct_type(f, force_readable=True)

    def __iter__(self):
        for f in self._file_list:
            yield self._get_correct_type(f)

    def __call__(self, path, ret_type=None, force_readable=False, force_writable=False, force_mode=None, encoding=None):
        return self._get_correct_type(path, ret_type=ret_type, force_readable=force_readable,
                                      force_writable=force_writable, force_mode=force_mode, encoding=encoding)


'''
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
'''

