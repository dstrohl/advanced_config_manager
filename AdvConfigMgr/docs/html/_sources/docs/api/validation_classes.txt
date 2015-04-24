
Validation Classes
==================

These classes are used by the :doc:`data_type_classes` to provide validation.  by default the data types only validate
that the data is actually of that datatype, however you can add any validation you wish.


Base Validation Class
---------------------
.. autoclass:: AdvConfigMgr.config_validation.ValidationsBase
    :members:


Pre-Configured Validation Classes
---------------------------------

.. automodule:: AdvConfigMgr.config_validation
    :members: ValidateStrEqual, ValidateStrExists, ValidateNumRange
