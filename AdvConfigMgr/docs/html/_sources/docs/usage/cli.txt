CLI Argument Management
=======================

The system can handle managing arguments passed via the CLI as well as ones in config files or databases.  When
configuring an option, you have the ability to pass a dictionary of parameters to the option keyword "cli_option".  This
dictionary will tell the system to allow that option to be configured by the CLI, defines the help for the cli, and
tells the system how to handle the response.

* flags: (required) a flag or list of flags to be accepted. (these must be unique across the system).

    .. note::  If only a single string is passed instead of a dictionary, it is assumed to be the flag and the rest of
        the data will be set at defaults.

* data_flag: If present, this will set the "store_true" or "store_false" action in argparse, this means that
    if True is set, and the cli flag is set, the option will be set to True, and vice-versa.  If a default
    is used, it must be a boolean.
* nargs: [int] This will allow that number of arguments to be added to a list config item, so for example,
    if nargs 3 is passed, the following argument would be treated as one:

    ::

        program.py -arg 1 3 4

    This would return ['1','2','3'], however if nargs 2 was passed, this would return ['1','2'] and the '3'
    would be treated as another positional argument.
    If a default is used in this case, it must be a list and have this many items.
* choices: a list of choices that are available (and will be validated against).  If a default is used, it
    must be present in the list.
* default: if not present, will use the option default, if present and None, will not have a default,
    if present and set to somethign, will use that as a default.
    .. note:: if a default is present, either passed or using the option default, it must also fit the other
    arguments.
* required: [True/False] this option MUST be passed on the command line.
* help: this is a descriotion string to be used on the command line.  if this is not present,
    the option description will be used.

::

    cli_option: ({'flags':['f', 'foo'],
                  'data_flag':False,
                  'nargs':2,
                  'choices':['bar','barr','b'],
                  'required':False,
                  'help':'This defines if this is fu or bar'})

