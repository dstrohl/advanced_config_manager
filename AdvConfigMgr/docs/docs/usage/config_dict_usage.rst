ConfigDict Usage
================

A ConfigDict object can be passed to the config manager (or gotten from the config manager) as a lighter weight
structure to store the configuration in.

ConfigDict Objects:
* Can be set to read only if desired.
* Will do interpolation of objects as needed.
* May be cascaded (ConfigDict objects may contain other ConfigDict objects).
* Can be accessed using all of the normal methods allowed to config manager sections and options
* Can be sub-referenced (i.e., you can set a variable to equal a section for easier config referencing).

* Will NOT raise signals on changes (though when resync'ed with the config manager, change signals will be raised.)
* Do NOT do any validation until re-synced with the config manager.
* Do NOT allow for creating any NEW options or sections.  (existing ones can be edited though).

