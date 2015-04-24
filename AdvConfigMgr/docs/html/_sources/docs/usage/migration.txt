Migration of Versions
=====================

The system can help with migrating the data between versions.  To handle migrations, first create a migration definition
dictionary. and pass it to the migration manager during section initialization.

Migrations are handled on a section by section basis, and are performed when running a read operation from a storage
manager (other than the cli manager)  So be aware that in a multi-storage environment,



This dictionary could have the following keys:

+---------------------+----------------+-----------------------------------------------------------------------------------+
| Key Name            |Data Type       | Description                                                                       |
+=====================+================+===================================================================================+
| section_name        | str            | The name of the section to be used.  can be omited only if a simple config is used|
+---------------------+----------------+-----------------------------------------------------------------------------------+
| stored_version_min  | str            | The version of the stored data to convert from, this requires at least one of the |
+---------------------+----------------+ version entries, and could have all three defined.                                +
| stored_version_max  | str            | If stored_version is None, (as oposed to omitted), this will be used to migrate   |
+---------------------+----------------+ from stored configs that do not have a version defined.                           +
| stored_version      | str            |                                                                                   |
+---------------------+----------------+-----------------------------------------------------------------------------------+
| live_version_min    | str            | The version of the stored data to convert from, this requires at least one of the |
+---------------------+----------------+ version entries and could have all three defined.                                 +
| live_version_max    | str            |                                                                                   |
+---------------------+----------------+                                                                                   +
| live_version        | str            |                                                                                   |
+---------------------+----------------+-----------------------------------------------------------------------------------+
| actions             | list of actions|  A list of actions with the option names and the actions to take for each.        |
+---------------------+----------------+-----------------------------------------------------------------------------------+
| keep_only           | bool           | If True, only options in the list will be kept, for record based storage all      |
|                     |                | others will be deleted (Defaults to False                                         |
+----------- ---------+----------------+-----------------------------------------------------------------------------------+
| action_class        | ActionClass    | a subclass of :py:class:`BaseMigrationActions` that is used to do the changes     |
+---------------------+----------------+-----------------------------------------------------------------------------------+


Actions
-------

This is a list of the actions that you want taken, each action record (dictionary or tuple) defines how you want to
handle an option (or set of options matching the filter).

The action records are either a dictionary of keys, or a tuple, these are passed to the action method as either a set
of args (if a tuple) or as a kward set (if a dictionary)

the action methods are in the MigrationActionClass, which you can also subclass and pass to in the migration definition
dictionary if you want to handle migrations differently.

An example of this is would be, if there is a migration action ('remove','my_option') the MigrationManager class will
call MigrationActionClass.remove('my_option').  This class method is responsible for carrying out the migration actions.

This could also have been passed as an action {'action':'remove','option_name':'my_option'}


Remove
++++++
These options will be removed and deleted from storage. [#rem1]_

Dict::

    {'action':'remove','option_name':<option_name>}

Tuple::

    ('remove','option_name')

Rename
++++++

This will rename the options.  you have the option to pass an interpolation string as well with this that can modify
the value of the string type options.

Dict::

    {'action':'rename',
    'option_name':<old option name>,
    'new_option_name':<new option name>,
    ['interpolation_str':<optional interpolation string>]}

Tuple::

    ('rename','old_option_name','new_option_name'[, 'interpolation_str'])

Copy
++++

This will copy an option and add it from another option.  This also allows copying from another section if a name is
passed using dot notation as well as an optional interpolation string.

Dict::

    {'action':'copy',
    'option_name':<existing option name>,
    'new_option_name',<new option name>,
    ['interpolation_str':<interpolation_string>]}

    {'action':'copy',
    'option_name':<existing section name.existing option name>,
    'new_option_name',<new option name>,
    ['interpolation_str':<interpolation_string>]}

Tuple::

    ('copy','old_option_name','new_option_name' [,'interpolation_str'])
    ('copy','old_section.old_option_name,'new_option_name' [, 'interpolation_str'])


Pass
++++

These will just be passed through, this is generally not needed unless the 'keep_only' flag is used, then these are
required for all options to be kept.

Dict::

    {'action':'pass',
    'option_name':<option_name>)

Tuple:

    ('pass','option_name')


Interpolate
+++++++++++

This runs the option through a simple interpolator, allowing for some simple conversions.

Dict::

    {'action':'interpolate',
    'option_name':<option_name>
    ['interpolation_str':<interpolation string>]}

Tuple::

    ('interpolate','option_name' [,'interpolation_str'])



Other
+++++

For more complex conversion needs, you can subclass the :py:class:`BaseMigrationActions` class and create your own
migrations.  Anything that is not in the above list will be passed to a method of the MigrationActions class method
matching the name of the action.  every action definition must have a 'action' key (or the first item in the tuple, and
an 'option_name' key (the second item in the tuple) that defines what options are sent.  along with the defined keys
a kwarg of 'value' will also be passed that is the current value of the option.

Some actions support glob type wildcards ('*', '?', '!', '[]'), (by default the 'remove', 'interpolate', and 'pass'
ones) Generally these would be ones that do not require changing the option name).

For interpolations, use '%(__current_value__)' for the current value, %(option_name), %(section_name.option_name) to
pull in othe values.

By default, options without actions will simply be passed through unless the "keep_only" flag is set.

.. rubric:: Footnotes

.. [#rem1] Only record based storage managers will delete these from the storage medium.  others will rely on the object
    not being present in the config since the entire config is re-written to the storage overwriting the old one.


