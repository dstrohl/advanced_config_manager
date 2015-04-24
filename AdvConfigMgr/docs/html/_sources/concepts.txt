Concepts
========

The Advanced Configuration Manager uses the following concepts

Configuration Manager
---------------------
This is the main object for the configuration manager.  All interaction would normally be with this object.

Sections
--------
A configuration is normally made up of sections, each section contains the options that are conifgured.  You can also
configure the system to not need sections, in which case everything will be in a single flat dictionary like structure.

Options
-------
The options are the end nodes of the system.  These are where you store your options, defaults, etc.  If you setup a
default they will return that default if no other value is set.

Interpolation
+++++++++++++
Interpolation allows one configuration variable to reference another.  so, for example, you could have options
"first_name" and "last_name", and have a third option with a value of "%(first_name) %(last_name)", which, when polled
would return the two names combined.

Storage
-------
This is where the options are stored.  There are various storage managers included, and an API for creating more.  For
example, in a typical option set, you may have two storage managers used.  a file storage manager for saving text files
and the cli manager for over-ridding some of the options with cli parameters.  In a more complex environment, you might
have three storage managers used.  the cli storage to define where the startup file is stored, a local text file to
configure the database connection parameters, and a database storage manager to save the majority of the items.

You might even have other storage managers setup for specific items such as user specific settings, group or team
settings, etc...

You can even use an initial storage and configuration file to configure later storage managers (such as the above
mentioned database managers).

Storage Names
+++++++++++++
Most of this is handled by setting storage names.  Each storage manager has a name.  each section has two parameters
that control what storage they can use.

*storage_write_to* can have the following settings:

    * '<name>': The name of the storage location to save to.
    * None: The section will be saved to the default location.
    * '-':  The section will NOT be saved in save_all operations (though it can still be manually saved to a storage
        location)
    * "*":  The section will be saved to ALL configured standard storage locations.  (not recommended in complex
        environments)

storage_read_from_only:
    * ['<name>', '<name>']: A list of names, this will only allow data read from these storage locations to be used for
        these sections.
    * None (default):  Options in storage will be always be used.

    .. note:: CLI options, if configured, will always overwrite data from storage.


