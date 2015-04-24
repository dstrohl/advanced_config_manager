Managing Data Storage Locations
===============================

Ths system can support multiple storage locations for the data, including handling data stored on local disk INI files,
databases, and even passing the data in dictionary or list format.

if nothing is configurred:

sections will have None in their storage manager space.
default eligable storage managers will be polled.
non default eligable storage managers can be requested.


if configured:
sections may have storage manager names in them
default managers can be polled and will pull if matched
