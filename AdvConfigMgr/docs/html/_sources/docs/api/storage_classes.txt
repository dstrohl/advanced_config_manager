
Storage Manager Classes
=======================

The system can store configuration data in multiple storage locations, the following classes are used by the system to
handle reading and writing from storage locations.

There are three types of storage locations that the system recognizes;

Read-Only:
    These are locations that do not ahve the ability to store data, Currently this is only the CLI manager.

Block-Based:
    These are locations that or write everything at once and do not have the ability to modify a single option.
    Examples of these are INI text files and the dictionary and string managers.

Record-Based:
    These are the most complex managers and are normally based on databases.  These have the ability to read or write
    options individually.


.. toctree::
   :maxdepth: 2

   configstorage