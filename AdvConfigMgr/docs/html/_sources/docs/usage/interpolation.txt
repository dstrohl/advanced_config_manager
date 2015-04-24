Interpolation Options
=====================

The interpolation system can handles replacement on the fly.  This is done within the options themselves, as well as
during migrations.

At its most basic, interpolation allows you to have a string that contains a key string that is replaced with the value
of another configuration option.  For example:

::
    # setup the configuration manager

    config = ConfigManager()
    config.add('section1')
    section1 = config['section1']

    # add some options for the data directory and data file

    section1['data_dir'] = 'my_path/data'
    section1['data_filename'] = 'my_data_file.db'

    # add an option that will return the full file and path for the database:

    section1['database'] = '%(data_dir)/%(data_filename)'

    # when you call the interpolated option
    section1['database']

    'mypath/data/my_data_file.db'

..note:: there are better approaches to handling paths in the system that woudl work better with cross platform systems,
    see :py:module:`pathlib`


Interpolation can also handle cross section variables, so you can use %(section_name.option_name) if needed, as well as
recursive variables where you are including a interpolated option in another interpolated option (up to a max of 10
levels).

if you need to use "%" in your option values, you can use escape it with "%%"

..note:: you can disable interpolation by passing None to the "interpolator" keyward arg for the :py:class:`ConfigManager`
