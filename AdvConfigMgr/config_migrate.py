__author__ = 'dstrohl'


from AdvConfigMgr.config_exceptions import Error



"""

Uses:

per section



migrations=[


"""

MAX_VERSION = '9999.9999.9999.9999'
MIN_VERSION = '0.0.0.0'


class ConfigMigrationError(Error):

    def __init__(self, version_from, version_to, section, option, msg):
        msg = 'Error converting [{}.{}]: {}, converting from {} to {}'.format(section, option, msg, version_from, version_to)
        super(ConfigMigrationError, self).__init__(msg)


class ConfigMigrationManager(object):

    def __init__(self):
        pass

    def needs_conversion(self, from_version, to_version):


class _VersionManager(object):

    def __init__(self, version_class, **kwargs):
        self._version_class = version_class

        if 'is' in kwargs:
            self.ver_is = self._get_version(kwargs.get('is', None))
        else:
            self.ver_min = self._get_version(kwargs.get('min', MIN_VERSION))
            self.ver_max = self._get_version(kwargs.get('max', MAX_VERSION))




    def _get_version(self, ver):

        if ver is None:
            return ver

        if isinstance(ver, str):
            return self._version_class(ver)

        if type(ver) is type(self._version_class):
            return ver

        return self._version_class(str(ver))



class BaseSectionMigrator(object):
    '''
    from_version_min = None
    from_version_max = None
    from_version = None

    to_version_min = None
    to_version_max = None
    to_version = None

    restrict_to_options = None
    remove_options = None
    require_options = None

    conversion_classes = None
    '''
    def __init__(self, conversion_manager, section_obj):
        self.conversion_manager = conversion_manager
        self.section = section_obj
        self.manager = section_obj.manager

        self.option_actions = {}


        self.from_version_max = self.manager._version_class(self.from_version_max)
        self.from_version_min = self.manager._version_class(self.from_version_min)

        self.to_version_max = self.manager._version_class(self.to_version_max)
        self.to_version_min = self.manager._version_class(self.to_version_min)




        self._update_local_attr('from_version_min', None)
        self._update_local_attr('from_version_max', None)

        self._update_local_attr('to_version_min', None)
        self._update_local_attr('to_version_max', None)



        self._update_local_attr('restrict_to_options', [])
        self._update_local_attr('remove_options', [])
        self._update_local_attr('require_options', [])

        self._update_local_attr('conversion_classes', [])




    def _update_local_attr(self, attr, val):
        if attr not in self.__dict__:
            setattr(self, attr, val)


    def _version_in(self, version):
        if isinstance(version, str):
            version = self.manager._version_class(version)




class BaseConverterClass(object):

    section = None
    manager = None

    section_conversion_manager = None
    conversion_manager = None

    def __init__(self, *options):
        self.options = options
        self.option = None
        self.old_value = None

    def convert(self, old_value):
        return old_value

    @property
    def conv_from(self):
        return self.conversion_manager.conv_from

    @property
    def conv_to(self):
        return self.conversion_manager.conv_to

    def conv(self, option, old_value):
        self.option = option
        self.old_value = old_value
        return self.convert(old_value)

    def warn(self, msg):
        self.conversion_manager.warn(self.conv_from, self.conv_to, self.section, self.option, msg)

    def error(self, msg):
        raise ConfigMigrationError(self.conv_from, self.conv_to, self.section, self.option, msg)


class DemoMultBy100Class(BaseConverterClass):

    def convert(self, old_value):
        if not isinstance(old_value, int):
            self.error('old value is not an int')
        return old_value * 100



