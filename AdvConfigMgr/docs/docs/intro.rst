
Introduction
============

The advanced configuration manager came from working on a project and realizing how important it was to deal with
configuration and settings, how many different places those settings were stored, how how complex it was to handle them.
I started out using a collection of tools (mostly execllent) to do this, including CLINT for CLI, ConfigParser for
configuration files, setting and setup files for global vars, and various custom scripts for other things.  I found that
I was often pulling the same kinds of things together, but there did not seem to be a package out there that handled
the entire thing.

Features
--------

The Advanced Configuration Manager will provide the following features:
    * defining configuration options within your modules
    * ease of access to options within your system
    * support for plugins to your system
    * storage of configuration options in multiple places
    * handling configuration options read from multiple places
    * default options
    * user changable options
    * locked options (non-changeable)
    * entry validation
    * interpolation of variables
    * clean API for adding features

    .. todo::
        * upgrade / downgrade scripts for fixing configs
        * logging and auditing
        * lightweight configuration reader, heavy manager.
        * support for authentication systems

The API allows for easilly adding the following items:
    * new configuration datatypes
    * new validations
    * new storage methods and systems
