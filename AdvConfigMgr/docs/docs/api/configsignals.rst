

Expected Signal types
=====================

Option Signals
--------------

pre_write:
    happens before anythign else in the write process including interpolation
    after validating that the data can be written though
        storage_manager, section, option, value
        returns value

post_write:
    happens after interpolation
        storage_manager, section, option, value
        returns new_value

pre_read:
    happens before anything else in the set process, parameters passed:
    after validations that the data can be read.
        section, option, current_value, value
        returns changed_new_value


post_read:
    happens after the data is actually saved in the system:
        section, option, new_value
        returns None

pre_get:
    happens before anythign else in the get including interpolation
        section, option, value
        returns value

post_get:
    happens after interpolation
        section, option, value
        returns new_value

pre_set:
    happens before anything else in the set process, parameters passed:
        section, option, current_value, value
        returns changed_new_value
post_set:
    happens after the data is actually saved in the system:
        section, option, value=new_value
        returns None

pre_create_option:
    happens before anythign else in the create process,
     section, options, value=kwargs
        returns kwargs


post_create_option:
    happens after the record is created
        section, option
        returns None


pre_clear:
    happens before record is cleared
        section, option, current_value, default_value, value=True
            returns Bool OK to clear

post_clear:
    happens after a record is cleared (but before it is deleted if keep_if_empty is False)
        section, option
            returns Bool OK to Delete
                (does not force delete)

pre_delete:
    happens before delete validations happen:
        section, option, value=True
            returns bool OK to delete
                (does not override validations)

post_delete:
    happens after item is deleted:
        section, option
            returns None


Section Signals
---------------

pre_create_section:
    happens before anythign else in the create process,
     section, value=kwargs
        returns kwargs


post_create_section:
    happens after the record is created
        section
        returns None

Storage Manager Signals
-----------------------

pre_storage_manager_read:
    happens after the data is read from storage and converted to a dict, but before it is saved.
        storage_manager, sections, override, value=data
            returns data

post storage_manager_read:
    happens after the data is saved to the system
        storage_manager, sections, sections_read, options_read

pre_storage_manager_write:
    happens after the data is read from the system in dict, but before it is written to storage
        storage_manager, sections, override, value=data
            returns data

post storage_manager_write:
    happens after the data is written to storage
        storage_manager, sections, sections_written, options_written


