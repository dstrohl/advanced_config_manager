'''
Created on Aug 10, 2014

@author: strohl
'''
__author__ = 'strohl'

import inspect
import pprint
from string import Formatter
import ast
import os
import logging


from AdvConfigMgr.utils.base_utils import get_before, get_between, swap
from AdvConfigMgr.utils.clicker_counter import Clicker
from AdvConfigMgr.utils.flag_manager import Flagger
from os import path

class IPFormatter(Formatter):
    def __init__(self, iph):
        self._iph = iph
        self._iph_properties = self._iph._exposed_properties
        self._iph_methods = self._iph._exposed_methods

    def get_value(self, key, args, kwargs):

        if isinstance(key, int):
            return args[key]
        else:
            test_key = get_before(key,'(')
            if key in self._iph_properties:
                return getattr(self._iph, key)

            if key in self._iph_methods:
                iph_meth = getattr(self._iph, key)
                return iph_meth()

            elif test_key in self._iph_methods:
                iph_meth = getattr(self._iph, test_key)
                iph_args, iph_kwargs = self._parse_args(get_between(key,'(',')'))
                return iph_meth(*iph_args, **iph_kwargs)
            else:
                return kwargs[key]


    def _parse_args(self,key_string):
        if key_string.endswith('=') or key_string.startswith('='):
            raise AttributeError('format key args must not start or end with "="')
        tmp_arg_list = key_string.split(',')
        tmp_arg_list_2 = []
        args_list = []
        kwargs_dict = {}
        skip_next = False
        for offset, arg in enumerate(tmp_arg_list):
            if arg == '=':
                tmp_arg_list_2.pop()
                tmp_str = tmp_arg_list[offset-1]+tmp_arg_list[offset]+tmp_arg_list[offset+1]
                tmp_arg_list_2.append(tmp_str)
                skip_next = True
            elif arg == '':
                pass

            else:
                if not skip_next:
                    tmp_arg_list_2.append(arg)


        for arg in tmp_arg_list_2:
            if '=' in arg:
                tmp_kwarg = arg.split('=')
                kwargs_dict[tmp_kwarg[0]] = ast.literal_eval(tmp_kwarg[1])
            else:
                args_list.append(arg)
                #args_list.append(ast.literal_eval(arg))

        return args_list, kwargs_dict


class Colorizer(object):
    ATTRIBUTES = dict(list(zip(['bold', 'dark', '', 'underline', 'blink', '',
                                'reverse', 'concealed'], list(range(1, 9)))))
    del ATTRIBUTES['']
    HIGHLIGHTS = dict(list(zip(['on_grey', 'on_red', 'on_green', 'on_yellow',
                                'on_blue', 'on_magenta', 'on_cyan', 'on_white'], list(range(40, 48)))))
    COLORS = dict(list(zip(['grey','red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'], list(range(30, 38)))))
    RESET = '\033[0m'

    def __init__(self, presets=None):
        self._presets = {}
        if presets:
            self._presets.update(presets)

    def __setitem__(self, key, value):
        self._presets[key] = value

    def __getitem__(self, item):
        try:
            return self(self._presets[item])
        except KeyError:
            raise KeyError('preset '+item+' not found in list of presets')

    def __call__(self, *args):
        color, on_color, attrs = self._param(*args)
        return self._colored(color, on_color, attrs)

    def _param(self, *args):

        if len(args) == 1:
            if isinstance(args[0], str):
                tmp_arg = args[0].replace(',',' ')
                if ' ' in tmp_arg:
                    args = tmp_arg.split()
            elif isinstance(args[0], (list, tuple)):
                args = args[0]

        attrib = []
        color = None
        on_color = None

        for a in args:
            if isinstance(a, str):
                a = a.lower()
                if a in self.ATTRIBUTES:
                    attrib.append(a)

                elif a in self.COLORS:
                    color = a

                elif a in self.HIGHLIGHTS:
                    on_color = a


        return color, on_color, attrib


    def _colored(self, color=None, on_color=None, attrs=None):
        """Generate Color String.

        Available text colors:
            red, green, yellow, blue, magenta, cyan, white.

        Available text highlights:
            on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_white.

        Available attributes:
            bold, dark, underline, blink, reverse, concealed.
        """
        text = ''
        reset = True
        if os.getenv('ANSI_COLORS_DISABLED') is None:
            fmt_str = '\033[%dm%s'
            if color is not None:
                text = fmt_str % (self.COLORS[color], text)
                reset = False

            if on_color is not None:
                text = fmt_str % (self.HIGHLIGHTS[on_color], text)
                reset = False

            if attrs is not None:
                if isinstance(attrs, str):
                    text = fmt_str % (self.ATTRIBUTES[attrs], text)
                    reset = False
                else:
                    for attr in attrs:
                        text = fmt_str % (self.ATTRIBUTES[attr], text)
                        reset = False

            if reset:
                text += self.RESET
        return text



    def colored(self, text, color=None, on_color=None, attrs=None):
        """Colorize text.

        Available text colors:
            red, green, yellow, blue, magenta, cyan, white.

        Available text highlights:
            on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_white.

        Available attributes:
            bold, dark, underline, blink, reverse, concealed.

        Example:
            colored('Hello, World!', 'red', 'on_grey', ['blue', 'blink'])
            colored('Hello, World!', 'green')
        """
        if os.getenv('ANSI_COLORS_DISABLED') is None:
            fmt_str = '\033[%dm%s'
            if color is not None:
                text = fmt_str % (self.COLORS[color], text)

            if on_color is not None:
                text = fmt_str % (self.HIGHLIGHTS[on_color], text)

            if attrs is not None:
                for attr in attrs:
                    text = fmt_str % (self.ATTRIBUTES[attr], text)

            text += self.RESET
        return text


class IndentedPrintHelper(object):

    _exposed_properties = ('crlf','stack','lf')
    _exposed_methods = ('counter','func_name','sep_line','new_line','color',
                        'f','c','nl','sep','co', 'color_preset', 'cp')

    _stack_format = '{caller_name} [{last_dir}.{file_name}:{line_num}] |'
    _stack_length_limits = {'__full_string__': {'max_length': 40,
                                                'pad_to_max': True,
                                                'end_string': '|'},
                                                'line_num': {'trim_priority': 0}
                            }
    _default_color_presets = {'prefix':'bold',
                              'var':'underline',
                              'critical':'red',
                              'minor':'grey'}
    #_render_queue = ''
    #_cw = ColorWrap()
    _color_string = None
    _currently_colored = False

    # accessible properties
    prefix = ''
    suffix = ''
    counter = Clicker()
    crlf = '\n'

    def __init__(self,
                 stack_format=None,
                 stack_length_limits=None,
                 color_presets=_default_color_presets):

        if stack_format:
            self._stack_format = stack_format
        if stack_length_limits:
            self._stack_length_limits = stack_length_limits
        #self.string_lookup = {}
        #self.flags = []
        #self.trouble_flag = False
        self._pp = pprint.PrettyPrinter(indent=3)

        self._ipf = IPFormatter(self)
        self._colorizer = Colorizer(presets=color_presets)
        self._templates = {}

    # ====================================
    # color
    # ====================================

    def color(self, color=None):
        return self._colorizer(color)

    def color_preset(self, preset):
        return self._colorizer[preset]

    # ====================================
    # lines and spaces
    # ====================================

    def new_line(self, new_line_count = 1):
        tmp_ret = ''
        for i in range(new_line_count):
            tmp_ret += self.crlf
        return tmp_ret

    @staticmethod
    def sep_line(sep_str='-', strlen=80):
        return ''.ljust(strlen, sep_str)

    @property
    def lf(self):
        return self.crlf

    # ====================================
    # System Data
    # ====================================

    @staticmethod
    def func_name(add_offset=0):
        import traceback
        tmp_trace = traceback.extract_stack(None)
        offset = len(tmp_trace) - 4 + add_offset
        return traceback.extract_stack(None)[offset][2]

    def stack(self):
        return self._parse_stack()

    # ====================================
    # template
    # ====================================

    def template_save(self, key, template):
        self._templates[key] = template
        return template

    def template(self, key, *args, **kwargs):
        return self.formatted(self._templates[key], *args, **kwargs)

    def __getitem__(self, item):
        return self.template(item)

    def __setitem__(self, key, value):
        self.template_save(key, value)

    # ====================================
    # formatting
    # ====================================

    def __call__(self, format_string, *args, **kwargs):
        return self.formatted(format_string, *args, **kwargs)

    def formatted(self, format_string, *args, **kwargs):
        format_string = self.prefix+format_string+self.suffix
        return self._ipf.format(format_string, *args, **kwargs)

    # ====================================
    # stack
    # ====================================


    def _parse_stack(self):
        off_path = 1
        off_line = 2
        off_attrib = 3
        tmp_attribs = dir(self)
        my_attribs = []
        format_kwargs = {}

        stack = inspect.stack()

        for s in tmp_attribs:
            if not s.startswith('__'):
                my_attribs.append(s)


        for s in stack:
            if not s[off_attrib] in my_attribs:

                format_kwargs['full_path'] = s[off_path]
                format_kwargs['line_num'] = s[off_line]
                format_kwargs['caller_name'] = s[off_attrib]
                break

        format_kwargs.update(self._parse_path(format_kwargs['full_path']))

        tmp_ret = self._stack_format.format(**format_kwargs)
        return tmp_ret

    def _parse_path(self, in_path):
        tmp_path, tmp_fn = path.split(in_path)
        tmp_path, tmp_dir = path.split(tmp_path)
        return {'start_path':tmp_path, 'last_dir':tmp_dir, 'file_name':tmp_fn}

    # ====================================
    # Shortcuts
    # ====================================

    def co(self, color=None):
        return self.color(color)

    def cp(self, preset):
        return self.color_preset(preset)

    def c(self, *args):
        return self.counter(*args)

    def sep(self, sep_str='-', strlen=80, indent=None):
        return self.sep_line(sep_str, strlen)

    def f(self, offset=0):
        return self.func_name(offset+1)


class IndentedPrinter(object):
    """
    The main class for the Indented Printing Module.
    """

    """
        Methods:
        
        That return itself are:  (these can be chained together)

            p(*objects [sep = ''] [end='\n']):
                Print the attached objects using the normal 'print' command.
            i( [indent = 0]):
                Sets the indent level
            a([indent = 1]):
                Adds [indent] to the current indent level
            s([indent = 1]):
                Subtracts [indent] from the current indent level
            ms([key = None], [indent = None]):
                Sets [indent] or the current indent level to a memory location at [key]
            mr([key = None]):
                Sets the current indent level to the one at memory location [key]
            push():
                Ads the current indent level to a FILO cache.
            pop():
                Returns the last indent level from the cache.
        
        The "g" method will return the string that would be printed by 'p' for use by logging functions or other programatic systems.
           g( *objects,  [sep = ''], [end = '\n']):
       
        Initialization parameters:
        
        IndentedPrint(
                        [indent_spaces],  (default = 3)
                        [silence],      (default = False)
                        [inc_stack],        (default = False)
                        [stack_format],        (default =)
                        [stack_length_limits],
                        [line_format],   (default - see below)
                        
        
            indent_spaces: The multiplier used for indenting.
                For example, if this is set at 5, the indent levels will be 5, 10, 15, 20...
                
            silence: used to silence all printing (does not impact using the "g" commend)
            
            caller: will include the called function or method in the string
            
            stack_format: defines the format of the called function or method (see below)
                            
            stack_length_limits: expects a dictionary that defines the max length of the stack printed section. (see below)
            
            line_format: uses a formatting string that details where the main sections are on the line.  See below for args and default
            
            
        Line Format args:
            {padding}
            {stack}
            {line}
            {end}
            
            default line format is: '{padding}{stack}{line}{end}'
            
        
        for the stack format string, allowed args are:
            {'full_path'}
            {'line_num'}
            {'caller_name'}
            {'start_path'}
            {'last_dir'}
            {'file_name'}

        Stack length limits dict options (with defaults):
            max_length = None
            min_length = 10
            do_not_show_length = 4
            pad_to_max  = False
            justification = 'left'   (options are 'left', 'right', and 'center')
            end_string = ''
            padding_string = ' '
            trim_string = '+'
            trim_priority = 1
                Trim priority is used to determine which objects should be trimmed.  first
                    - priority of 0 indicates no trimming allowed
                    - fields with the same trim priority will be trimmed to equal lengths to fit the overall max string length
                    - after set 1 is trimmed to all min length, set 2 is trimmed and so on.
                    - if all trim priority sets are trimmed to min length, and the string is still too long, everything is trimmed equally below the min length other than lines marked with a 0.
                    - if strings fall below "do_not_show_length", they are excluded.
                    - if final string is still over __full_string__.max_length, the full string will be trimmed to max_length
                    
        
            
        Stack length limits dict definition (and defaults)
            {'__full_string__': {'max_length':40,
                            'pad_to_max':True,
                            'end_string':'|',
            'line_num': {'trim_priority':0}        
            'caller_name': {'max_length':15,
            'last_dir': {'max_length':40,
            'file_name': {'max_length':40,
                          }
    """

    _current_indent = 0
    _line_format = '{prefix}{padding}{line}{suffix}'
    _enable_flags = True

    _prefix = ''
    _suffix = ''

    _print_buffer = ''

    _logger_default_formatter = '%(name)s - %(levelname)s - %(message)s'
    _current_logging_level = logging.INFO
    _logger_levels = {
        'critical': logging.ERROR,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }

    def __init__(self,
                 indent_spaces = 5,
                 silence = False,
                 line_format=_line_format,
                 stack_format = None,
                 stack_length_limits = None,
                 prefix=_prefix,
                 suffix=_suffix,
                 logger=None):

        self._indent_spaces = indent_spaces
        self._silence_flag = silence
        self._indent_mems = {}
        self._pop_queue = []
        self._string_lookup = {}

        self._line_format = line_format
        self._trouble_flag = False

        self._log_manager = None
        self._pp = pprint.PrettyPrinter(indent=3)
        self._iph = IndentedPrintHelper(stack_format, stack_length_limits)
        self._flag_manager = None

        # accessible attributes
        self._prefix = prefix
        self._suffix = suffix

        if logger:
            self.set_logger(logger=logger)

    # ====================================
    # pre-suffix methods
    # ====================================

    def set_suffix(self, suffix):
        self._suffix = suffix
        return self

    def set_prefix(self, prefix):
        self._prefix = prefix
        return self

    @property
    def suffix(self):
        if self._suffix:
            return self._iph(self._suffix)
        else:
            return ''

    @property
    def prefix(self):
        if self._prefix:
            return self._iph(self._prefix)
        else:
            return ''

    # ====================================
    # indent control methods
    # ====================================

    def indent(self, indent=0):
        self._current_indent = indent
        return self

    def indent_add(self, indent=1):
        self._current_indent += indent
        return self

    def indent_sub(self, indent=1):
        self._current_indent -= indent
        if self._current_indent < 0:
            self._current_indent = 0
        return self

    def indent_mem_save(self, key=None, indent=None):
        if indent is not None:
            tmp_indent = indent
        else:
            tmp_indent = self._current_indent

        if key:
            self._indent_mems[key] = tmp_indent
        else:
            self._pop_queue.append(tmp_indent)
        return self

    def indent_mem(self, key=None):
        if key:
            try:
                self._current_indent = self._indent_mems[key]
            except KeyError:
                pass
        else:
            self.pop()
        return self

    def push(self):
        self._pop_queue.append(self._current_indent)
        return self

    def pop(self):
        self._current_indent = self._pop_queue.pop()
        return self

    # ====================================
    # logger integration
    # ====================================

    @property
    def _logger(self):
        if not self._log_manager:
            raise AttributeError('logger not defined or initialized')
        return self._log_manager

    @property
    def _check_for_logger(self):
        if self._log_manager:
            return True
        return False

    def set_logger(self, logger=None, logger_format=None, logging_disp_level=None):
        """
        sets up the logger if integration with the logging module is desired.
        :param logger: can be a logger instance or a string,  if this is  a string, a new default logging instance
        is created with the string as the name.
        :param logger_format: if a string is passed in the logger field, this can be set to generate a logger formatter
        using the string.
        :return:
        """
        if logger is None:
            logger = 'IP Log'

        if isinstance(logger, logging.Logger):
            self._log_manager = logger
        else:
            self._log_manager = logging.getLogger(str(logger))
            if not logger_format:
                logger_format = self._logger_default_formatter

            ch = logging.StreamHandler()
            fm = logging.Formatter(logger_format)
            ch.setFormatter(fm)
            self._logger.addHandler(ch)

        if logging_disp_level:
            self.set_logger_level(logging_disp_level)
        return self

    def set_logger_disp_level(self, level):
        self._logger.setLevel(self._convert_log_level(level))
        return self

    def log_level(self, level):
        self._current_logging_level = self._convert_log_level(level)

    def _convert_log_level(self, level):

        if isinstance(level, str):
            level = level.lower()
            ret_level = self._logger_levels[level]
            return ret_level
        else:
            return level

    def _log(self, log_level, msg):
        log_level = self._convert_log_level(log_level)
        if self._log_manager and self._logger.isEnabledFor(log_level):
            self._logger.log(log_level, msg)

    def critical(self, *args):
        self.println(*args,log_level=logging.CRITICAL)
        return self

    def error(self, *args):
        self.println(*args,log_level=logging.ERROR)
        return self

    def warning(self, *args):
        self.println(*args,log_level=logging.WARNING)
        return self

    def info(self, *args):
        self.println(*args,log_level=logging.INFO)
        return self

    def debug(self, *args):
        self.println(*args,log_level=logging.DEBUG)
        return self



    # ====================================
    # printing methods
    # ====================================

    def buffer(self, *args):
        self._print_buffer = self._make_line(self._print_buffer, *args)
        return self

    def print(self, *args , **kwargs):
        kwargs['end'] = ''
        self._print(*args, **kwargs)
        return self

    def println(self, *args , **kwargs):
        kwargs['end'] = '\n'
        self._print(self._print_buffer, *args, **kwargs)
        self._print_buffer = ''
        return self

    def get(self, *args, **kwargs):
        if not self._silence:
            return self._make_string(*args, **kwargs)
        else:
            return ''

    def getln(self, *args, **kwargs):
        if not self._silence:
            tmp_str = self._print_buffer
            self._print_buffer = ''
            return self._make_string(tmp_str, *args, **kwargs)
        else:
            self._print_buffer = ''
            return ''


    def _print(self, *args , end = '', **kwargs):
        """
        prints the content to stdout

        NOTE: should not generate any strings or content (other than \n or console only content)
        """
        self._trouble_print()
        if not self._silence:
            print_str = ''
            if args:
                print_str = self._make_string(*args, **kwargs)

            if self._check_for_logger:
                log_level = kwargs.pop('log_level',self._current_logging_level)
                self._log(log_level, print_str)
            else:
                print('', end=end)

    def _make_string(self, *args , **kwargs):
        """
        generates the string to be printed
        """
        sep = kwargs.get('sep', '')
        skip_helper = kwargs.get('skip_helper',False)


        padding = ''
        for i in range(self._current_indent * self._indent_spaces): padding += ' '

        line = self._make_line(*args, **kwargs)

        return self._line_format.format(padding = padding,
                                        line = line,
                                        prefix = self.prefix,
                                        suffix = self.suffix)

    def _make_line(self, *args, **kwargs):
        """
        generates the line to be printed (text without pre/suffix or indent)
        """
        sep = kwargs.get('sep', '')
        skip_helper = kwargs.get('skip_helper',False)

        line = ''
        for s in args:
            if line != '':
                line += sep

            if isinstance(s, str):
                line += self._iph(s)
            else:
                line += str(s)

        return line

    # ====================================
    # support methods
    # ====================================


    def troubleshoot(self, troubleshoot = False):
        self._trouble_flag = troubleshoot

    def _trouble_print(self):
        if self._trouble_flag:
            print('Indent Spaces  : ', self._indent_spaces)
            print('Current Indent : ', self._current_indent)
            print('Silence        : ', self._silence)
            print('Memories       : ', self._indent_mems)
            print('Push Queue     : ', self._pop_queue)
            print('Flags          :')
            print('    Current    : ', str(self._flagger.cur))
            print('    Include    : ', str(self._flagger.inc))
            print('    Exclude    : ', str(self._flagger.exc))

    # ====================================
    # flag methods
    # ====================================

    @property
    def _flagger(self):
        if self._flag_manager == None:
            self._flag_manager = Flagger()
        return self._flag_manager

    '''
    @property
    def _flags_in_use(self):
        if self._enable_flags:
            if self._flag_manager == None:
                return False
            else:
                return True

        return False
    '''

    def include_if_flag(self, flags):
        self._flagger(include=flags)
        return self

    def exclude_if_flags(self, flags):
        self._flagger(exclude=flags)
        return self

    def current_flags(self, flags):
        self._flagger(flags)
        return self

    def toggle_flag_enable(self, new_state):
        swap(self._enable_flags)
        return self

    @property
    def _check_flags(self):
        if self._flag_manager is not None:
            return self._flagger()
        else:
            return True

    # ====================================
    # silencer
    # ====================================

    @property
    def _silence(self):
        if self._silence_flag:
            return True
        if not self._check_flags:
            return True
        return False

    def toggle_silent(self, silence=None):
        """
        will toggle silent on if off, or vice-versa, unless the silence flag is set, in which case it will follow the
        flag

        .. note:: Shortcutted to si

        :param silence: True/False, to silence the IP process.
        :return:
        """
        if silence:
            self._silence_flag = silence
        else:
            self._silence_flag = swap(self._silence)
        return self

    # ====================================
    # call parser
    # ====================================

    def __call__(self, *args):
        """
        same as println()
        """
        return self.println(*args)


    # ====================================
    # Shortcuts
    # ====================================

    def co(self, color=None):
        """
        Shortcut for :meth:`IndentedPrinter.color`
        """
        return self.color(color)

    def ca(self, count_diff=1, counter_key=None):
        return self.counter_add(count_diff, counter_key)

    def cs(self, count_diff=1, counter_key=None):
        return self.counter_sub(count_diff, counter_key)

    def cc(self, count=0, counter_key=None):
        return self.counter_clear(count, counter_key)

    @property
    def c(self):
        return self.get_counter()

    def p(self, *args , **kwargs):
        return self.print(*args, **kwargs)

    def pl(self, *args , **kwargs):
        return self.println(*args, **kwargs)

    def ks(self, key, *args, **kwargs):
        return self.keystring_save(key, *args, **kwargs)

    def kp(self, key):
        return self.keystring_print(key)

    def pp(self, *args, **kwargs):
        return self.pretty_print(*args, **kwargs)

    def lp(self, *args, **kwargs):
        return self.println(*args, **kwargs)

    def nl(self, new_line_count=1):
        return self.new_line(new_line_count)

    def i(self, indent=0):
        return self.indent(indent)

    def a(self, indent=1):
        return self.indent_add(indent)

    def s(self, indent=1):
        return self.indent_sub(indent)

    def ms(self, key=None, indent=None):
        return self.indent_mem_save(key, indent)

    def mr(self, key=None):
        return self.indent_mem(key)

    def sep(self, sep_str='-', strlen=80, indent=None):
        return self.sep_line(sep_str, strlen, indent)

    def f(self, offset=0):
        return self.func_name(offset)

    def fi(self, flags):
        return self.include_if_flag(flags)

    def fe(self, flags):
        return self.exclude_if_flags(flags)

    def fc(self, flags):
        return self.current_flags(flags)

    def cr(self, *args):
        return self.critical(*args)

    def er(self, *args):
        return self.error(*args)

    def wa(self, *args):
        return self.warning(*args)

    def inf(self, *args):
        return self.info(*args)

    def de(self, *args):
        return self.debug(*args)

    def b(self, *args):
        return self.buffer(*args)

    def si(self, *args, **kwargs):
        return self.toggle_silent(*args, **kwargs)