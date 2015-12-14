
Example Usages
==============

Initial setup::

    from AdvConfigMgr import *

    class MyConfigManager(AdvConfigMgr.ConfigManager):
        _storage_plugins = (MongoStorage, ConfigFileStorage)


    cfg = ConfigDict()
    cfg_mgr = MyConfigManager(cfg)
    cfg_mgr['_system.storage.file.name'] = 'my_program_config.ini'
    cfg_mgr['_system.storage.file.path'] = 'my_program_config.ini'


    class MyProgram(object):
        plugins = load_plugins()    # make sure all plugins, sections, etc have loaded before calling initial_load().
        cfg_mgr.add(plugins)

        my_config_options = dict(
            option1 = 'test',
            option2 = 12345',
            option3 = ConfigOption(default='blah', storage='foo'),
        )


        system_config = cfg_mgr.add_section('system', default_option=)

        system_config['config_path'] = ConfigOption(default=Path('$SYS_MAIN_PATH'),
                                                    storage=[{'cli': {'param': 'path', 'npargs':'+'),
                                                             {'file'}])




        cfg_mgr.register_signal('post_load', post_load_method)
        cfg_mgr.register_signal('post_change', post_change_method)

        def __init__(self):
            self.config.load()

        def post_load_method(self, cfg_mgr, storage_name, sections, flags)
            if 'restart_db' in flags:
                self.restart_database()

        def post_change_method(self, cfg_mgr, section, option)
            cfg_mgr.save(section=section)

    class OtherProgramClass(object):
        sec_cfg_mgr = cfg_mgr.add_section('other_section')
        sec_cfg_mgr['option1'] = 'foobar'
        sec_cfg_mgr['option2'] = ConfigOption(<options>)

        config = sec_cfg_mgr.config()


        def my_method(self):
            print('situation normal, all '+self.config.option1)







    class PluginBase(object):





    class MyPlugin(PluginBase):
        name = 'my plugin'
        version = 1.2

        cli_section = dict(
            name='mpi',
            description='my plugin section',
        )

        config_options = [
            ConfigOption('option1', default='test', cli_settings={'param': 'opt1', 'npargs': 'n'})
            ConfigOption('option2', default='foo', flag_on_user_change='restart', storage='file')
            ConfigOption('option3', default=123, storage='mongo', flag=[('system_load','restart_db')]
        ]

        with plugin_config.defaults(storage='file', flag_on_user_change='restart') as tmp_cfg:
            tmp_cfg.add('option4', 'bar')
            tmp_cfg.option5 = test1

        # or

        config_options = dict(
            option1 = 'test',
            option2 = 'foo',
            option3 = 123
        )

