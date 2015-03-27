Usage
=====
Using the Configuration Manager can be simple, the minimum that you need to do is:
* Import ConfigurationManager() and instantiate it.
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
    sec = config['my_section']
    sec.add(my_option1='default_value', my_option2=1234, my_option3=['item1', 'item2'])
    # there are more ways of setting options as well

Using Options
-------------

::

    # reading the option
    temp_var = sec['my_option1']

    # setting the option value
    sec['my_option'] = 'new value'

    # clearing the option and using the default value
    del ['my_option']


Saving Options to a file
------------------------

::

    # saving to a storage location such as a file can be as easy as
    config.save()

    