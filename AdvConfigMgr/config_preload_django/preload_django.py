__author__ = 'dstrohl'

__all__ = ['dcm_factory']

from ..advconfigmgr import ConfigManager
from copy import copy, deepcopy
from .config_django_settings import *


class DjangoConfigManager(ConfigManager):
    _DEFAULT_CLI_MANAGER = None
    _default_cli_name = None
    _autosave_names = ['*', ]
    _autoload_names = ['local', ]


class DcmFactory(object):

    def __init__(self):
        self._DCM = None

    def get_dcm(self, ini_file_name=None, base_options=None, version=None):
        """
        instantiates the DjangoConfigManager with some base Django Options

        all options passed will be added to the "settings" section.
        :param ini_file_name: String file name and path of the ini file to read from.
        :param base_options: list of full option dictionaries or single dictionary of options.
            if a single dict is passed, it is assuemd to be a simple option dict, so if you
            need to pass a single full option dictionary, you need to enclose it in a list.
        :param version: version string
        :return: returns a DjangoConfigManager instance loaded with initial options.
        """

        if self._DCM is None:

            storage_config = dict(file={
                'storage_name': 'local',
                'filename': ini_file_name,
            })


            if base_options is not None:
                tmp_opts = []
                if isinstance(base_options, dict):
                    for name, value in base_options.items():
                        tmp_o = dict(name=name, default_value=value)
                        tmp_opts.append(tmp_o)

                django_options = merge_lists_of_dicts(base_options, _DJANGO_DEFAULT_OPTIONS, 'name')

                _DJANGO_SETTINGS_SECTION['options'] = django_options

            self._DCM = DjangoConfigManager(version=version,
                                            storage_config=storage_config,
                                            section_list=[_DCM_SETTINGS_SECTION, _DJANGO_SETTINGS_SECTION])

            # self._DCM.read()

        return self._DCM

dcm_factory = DcmFactory()


def merge_lists_of_dicts(source, target, key, source_default=None, target_default=None):
    """
    assumes two lists of dictionaries
    merge source into target, replacing anythng in target that exists, keeping the order of target, recortds in the
    source that are not in the target will be added at the end.

    if a default dictionary is passed, any empty fields in the source or target will be filled in with the default
    fields.

    :param list source:
    :param list target:
    :param str key:
    :param dict source_default:
    :param dict target_default:
    :return:
    """
    tmp_ret = []

    tmp_source = {}
    for s in source:
        if source_default is not None:
            tmp_item = deepcopy(source_default)
            tmp_item.update(s)
        else:
            tmp_item = s

        tmp_source[s[key]] = tmp_item

    for t in target:
        if target_default is not None:
            tmp_item = deepcopy(target_default)
            tmp_item.update(t)
        else:
            tmp_item = t

        tmp_item.update(tmp_source.pop(t[key], {}))

        tmp_ret.append(tmp_item)

    for key, item in tmp_source.items():
        tmp_ret.append(item)

    return tmp_ret