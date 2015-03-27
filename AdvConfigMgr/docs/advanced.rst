Advanced Usage
==============

Using CLI arguments
-------------------


            .. note:: The CLI is handed with :class:`argparse` so all options should be able to be matched to those for
                detailed questions, not all options are supported though.

            * flags: (required) a flag or list of flags to be accepted. (these must be unique across the system).
                Note:  The '-' that is required for :class:`argpars` will be automatically added and does not need to
                be there.

                .. note::  If only a single string is passed, it is assumed to be the flag

            * data_flag: If present, this will set the "store_true" or "store_false" action in argparse, this means that
                if True is set, and the cli flag is set, the option will be set to True, and vice-versa.  If a default
                is used, it must be a boolean.
            * nargs: [int] This will allow that number of arguments to be added to a list config item, so for example,
                if nargs 3 is passed, the following argument would be treated as one:
                    -arg 1 3 4
                and would return ['1','2','3'], however if nargs 2 was passed, this would return ['1','2'] and the '3'
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

                cli_option: ({'flags':['f', 'foo'],
                              'data_flag':False,
                              'nargs':2,
                              'choices':['bar','barr','b'],
                              'required':False,
                              'help':'This defines if this is fu or bar'})


Defining additional storage locations
-------------------------------------

Interpolation
-------------

Validation
----------

