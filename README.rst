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

You will also need to add some taskview settings for the new signups view:

::

    signup:
        additional_actions:
            - AddDefaultUsersToProject
            - NewProjectDefaultNetwork
        notifications:
            standard:
                EmailNotification:
                    emails:
                        - signups@example.com
                RTNotification:
                    queue: signups
            error:
                EmailNotification:
                    emails:
                        - signups@example.com
                RTNotification:
                    queue: signups
        default_region: RegionOne
        # If 'None' (null in yaml), will default to domain as parent.
        # If domain isn't set explicity, will service user domain (see KEYSTONE).
        default_parent_id: null
        setup_network: True


Once active, and if debug is turned on, you can see the endpoint and test it with the browsable django-rest-framework api.
