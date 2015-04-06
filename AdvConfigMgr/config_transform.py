__author__ = 'dstrohl'

__all__ = ['Xform']

from AdvConfigMgr.utils import get_after, get_before
from unicodedata import normalize
from AdvConfigMgr.utils.unset import _UNSET

class Xform(object):

    def __init__(self, sec_opt_sep='.', glob_chars='*?[]!', glob_no_chars='_'):
        self._section_cache = {}
        self._section_glob_cache = {}
        self._option_cache = {}
        self._option_glob_cache = {}
        self._sec_opt_sep = sec_opt_sep
        self._def_glob_chars = glob_chars
        self._def_no_glob_chars = glob_no_chars
        self._last_option = _UNSET
        self._last_section = _UNSET
        self._last_dot_not = _UNSET

    def option_x_form(self, optionstr, extra_allowed='_', glob=False):
        """
        Will transform the option name string as needed, by default this will slugify and lowercase the string.

        This also caches the return to minimize the times through the transformer.

        This can be overridden as desired.
        """
        if glob:
            try:
                return self._option_glob_cache[optionstr]
            except KeyError:
                tmp_ret = self.slugify(optionstr, allowed=self._def_glob_chars, case='lower', punct_replace='_')
                self._option_glob_cache[optionstr] = tmp_ret
                return tmp_ret
        else:
            try:
                return self._option_cache[optionstr]
            except KeyError:
                tmp_ret = self.slugify(optionstr, allowed=self._def_no_glob_chars, case='lower', punct_replace='_')
                self._option_cache[optionstr] = tmp_ret
                return tmp_ret

    def section_x_form(self, sectionstr, extra_allowed='_', glob=False):
        """
        Will transform the section name string as needed, by default this will slugify and uppercase the string.

        This also caches the return to minimize the times through the transformer.

        This can be overridden as desired.
        """
        if glob:
            try:
                return self._section_glob_cache[sectionstr]
            except KeyError:
                tmp_ret = self.slugify(sectionstr, allowed=self._def_glob_chars, case='upper', punct_replace='_')
                self._section_glob_cache[sectionstr] = tmp_ret
                return tmp_ret
        else:
            try:
                return self._section_cache[sectionstr]
            except KeyError:
                tmp_ret = self.slugify(sectionstr, allowed=self._def_no_glob_chars, case='upper', punct_replace='_')
                self._section_cache[sectionstr] = tmp_ret
                return tmp_ret

    def is_dot_notation(self, name):
        if self._sec_opt_sep is not None and self._sec_opt_sep in name:
            return True
        if self._sec_opt_sep is None and self._sec_opt_sep in name:
            msg = 'Dot Notation disabled : {}'.format(name)
            raise AttributeError(msg)
        return False

    def full(self, name=_UNSET, extra_allowed=None, glob=False,
             option_or_section='option', section=_UNSET, option=_UNSET):
        tmp_check, tmp_section, tmp_option = self.full_both(name, extra_allowed=extra_allowed, glob=glob,
                                                            option_or_section=option_or_section, section=section,
                                                            option=option)
        return '{}.{}'.format(tmp_section, tmp_option)

    def full_check(self, name=_UNSET, extra_allowed=None, glob=False,
                   option_or_section='option', section=_UNSET, option=_UNSET):

        tmp_check, tmp_section, tmp_option = self.full_both(name, extra_allowed=extra_allowed, glob=glob,
                                                            option_or_section=option_or_section,
                                                            section=section, option=option)

        return tmp_check, '{}.{}'.format(tmp_section, tmp_option)

    def both(self, name=_UNSET, extra_allowed=None, glob=False,
                   option_or_section='option', section=_UNSET, option=_UNSET):

        tmp_check, tmp_section, tmp_option = self.full_both(name, extra_allowed=extra_allowed, glob=glob,
                                                            option_or_section=option_or_section,
                                                            section=section, option=option)
        return tmp_section, tmp_option

    def both_check(self, name=_UNSET, extra_allowed=None, glob=False,
                   option_or_section='option', section=_UNSET, option=_UNSET):

        tmp_check = False
        if name is None:
            return None, None

        if option_or_section == 'option':
            tmp_option = self.option(name, extra_allowed=extra_allowed, glob=glob)
            tmp_section = self.section()
            if tmp_section is _UNSET:
                if section is not _UNSET:
                    tmp_section = self.section(section, extra_allowed=extra_allowed, glob=glob)
                else:
                    return False, None, tmp_option
            else:
                tmp_check = True
        else:
            tmp_section = self.section(name, extra_allowed=extra_allowed, glob=glob)
            tmp_option = self.option()
            if tmp_option is _UNSET:
                if option is not _UNSET:
                    tmp_option = self.option(option, extra_allowed=extra_allowed, glob=glob)
                else:
                    return False, None, tmp_section
            else:
                tmp_check = True

        return tmp_check, tmp_section, tmp_option

    def option(self, option=_UNSET, extra_allowed=None, glob=False):
        if option is _UNSET:
            return self.option_x_form(self._last_option, extra_allowed=extra_allowed, glob=glob)

        if isinstance(option, str):
            if self.is_dot_notation(option):
                self._last_section = get_before(option, self._sec_opt_sep)
                return self.option_x_form(get_after(option, self._sec_opt_sep), extra_allowed=extra_allowed, glob=glob)
            else:
                self._last_section = _UNSET
                return self.option_x_form(option, extra_allowed=extra_allowed, glob=glob)
        else:
            return None

    def section(self, section=_UNSET, extra_allowed=None, glob=False):
        if section is _UNSET:
            return self.section_x_form(self._last_section, extra_allowed=extra_allowed, glob=glob)

        if isinstance(section, str):
            if self.is_dot_notation(section):
                self._last_option = get_after(section, self._sec_opt_sep)
                return self.section_x_form(get_before(section, self._sec_opt_sep),
                                           extra_allowed=extra_allowed, glob=glob)
            else:
                self._last_option = _UNSET
                return self.section_x_form(section, extra_allowed=extra_allowed, glob=glob)
        else:
            return None

    @staticmethod
    def slugify(text, delim='_', case='lower', allowed=None, punct_replace='', encode=None):
        """
        generates a simpler text string.

        :param text:
        :param delim: a string used to delimit words
        :param case: ['lower'/'upper'/'no_change']
        :param allowed: a string of characters allowed that will not be replaced.  (other than normal alpha-numeric
            which are never replaced.
        :param punct_replace: a string used to replace punction characters, if '', the characters will be deleted.
        :param encode: Will encode the result in this format.
        :return:
        """

        if text is None or not isinstance(text, str):
            return text

        punct = '[\t!"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+'
        if allowed is not None:
            for c in allowed:
                punct = punct.replace(c, '')

        result = []

        for word in text.split():
            word = normalize('NFKD', word)
            for c in punct:
                word = word.replace(c, punct_replace)
            result.append(word)

        delim = str(delim)
        # print('sluggify results: ', result)
        text_out = delim.join(result)

        if encode is not None:
            text_out.encode(encode, 'ignore')

        if case == 'lower':
            return text_out.lower()
        elif case == 'upper':
            return text_out.upper()
        else:
            return text_out
