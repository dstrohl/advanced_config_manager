
Example Usages
==============

Initial setup::

    import AdvConfigMgr

    class MyConfigManager(AdvConfigMgr.ConfigManager):
        _storage_plugins = (MongoStorage, ConfigFileStorage)
        _storage_settings['file.path'] = '{system.config_path}'
        _storage_settings['file.name'] = _storage_.setting2

        _sections.default.setting1 = True
        _sections.default.setting2 = 'foo'

        _options.default.setting1 = 'bar'




    cfg = {}
    cfg_mgr = MyConfigManager(cfg)



    class MyProgram(object):


    class MyPluginRegister(object):



    class MyPlugin(object):
        version = 1.2
        config_options = [
            ConfigOption('goo', default='ber', type='string')
            ConfigOption(

        ]
            option1 = 'goo'
            option2 = 'ber'
            option3 =
        )
        config_cli_options = dict(

        )


