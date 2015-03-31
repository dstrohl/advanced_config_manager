.. Advanced Configuration Manager documentation master file, created by
   sphinx-quickstart on Thu Mar 26 06:13:46 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Advanced Configuration Manager's documentation!
==========================================================

This is a configuration management plugin that helps with complex applications managing their basic settings.  Often,
these settings are stored as global vars in setup.py, settings.py, __init__.py files, but this does not scale well,
nor is it easilly managable from within an app from a conifugration screen.  This plugin helps with all of this.

Contents:

.. toctree::
   :maxdepth: 2

   docs/intro
   docs/concepts
   docs/usage/tutorial
   docs/api/configuration
   docs/extending/extending
   docs/license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Build / Test Status
===================
From Travis-CI.org (this is probably red since it is testing all versions of Python against it.  sorry, it only works
with 3.4 for now).

.. image:: https://travis-ci.org/dstrohl/advanced_config_manager.svg?branch=master
    :target: https://travis-ci.org/dstrohl/advanced_config_manager