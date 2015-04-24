Usage
=====
Using the Configuration Manager can be simple, the minimum that you need to do is:

    * Import :py:class:`ConfigManager` and instantiate it.
    * Define the options that you want to use
    * Reference the options


Setup the Manager
-----------------

::

    from AdvConfigMgr import ConfigManager
    config = ConfigManager()

Defining Options
----------------
::

    # define the section for the options
    config.add('my_section')

    # define the options within the section
    config['my_section'].add(my_option1='default_value', my_option2=1234, my_option3=['item1', 'item2'])
    # there are more ways of setting options as well

    # if no advanced features are needed, often this will be handled more like this
    section_config = config['my_section']

    ...

    section_config['option1'] = value
    section_config['option2'] = another_value
    section_config['option3'] = still_another_value


Using Options
-------------

::


    # to save typing, we can assign the section to a variable:
    sec = config['my_section']

    # reading the option
    temp_var = sec['my_option1']

    # setting the option value
    sec['my_option'] = 'new value'

    # clearing the option and using the default value
    del ['my_option']

    # you can also do something like this
    tmp_var = config['my_section']['my_option1']

    # or even this if it works better for you
    tmp_var = config['my_section.my_option']


Saving Options to a file
------------------------

::

    # saving to a storage location such as a file can be as easy as
    config.write(file='myfile.ini')

    # and readign it again later
    config.read(file='myfile.ini')

    # the filename can also be set during the initial setup, in which case you can simply do:
    config.write()
    config.read()

Advanced Features and configuration
-----------------------------------

There are many advanced features and configuration options that are available if needed, as well as several ways of
extending the system.

