StackTask-Odoo is a plugin for StackTask which adds a few actions and views specific to the Odoo ERP system. These views can then be setup as active for you users, and the actions can be used with your existing views. Or just as easily extend these views and actions for your own development.

Installing
====================

To install:

::

    python setup.py install

or

::

    pip install stacktask-odoo


After installation is complete add 'odoo_actions' and 'odoo_views' to your ADDITIONAL_APPS in the StackTask conf.

You can then use the Odoo actions as part of your StackTask workflows, and setup the Odoo views from this package in your ACTIVE_TASKVIEWS.