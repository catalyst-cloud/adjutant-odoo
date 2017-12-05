Adjutant-Odoo is a plugin for Adjutant which adds a few actions and views
specific to the Odoo ERP system. These views can then be setup as active for
your users, and the actions can be used with your existing taskviews. Or just
as easily extend these views and actions for your own development.

Installing
====================

To install:

::

    python setup.py install

or

::

    pip install adjutant-odoo


After installation is complete add `odoo_actions` and `odoo_views` to your
ADDITIONAL_APPS in the Adjutant conf.

You can then use the Odoo actions as part of your Adjutant workflows, and
setup the Odoo views from this package in your ACTIVE_TASKVIEWS. For example
to introduce signups backed to Odoo you'd replace your other signup view in
ACTIVE_TASKVIEWS with `OpenStackSignUp`.

You will also need to add some taskview settings for the new signups view:

::

    signup:
        additional_actions:
            - NewProjectDefaultNetworkAction
        notifications:
            standard:
                EmailNotification:
                    emails:
                        - signups@example.com
            error:
                EmailNotification:
                    emails:
                        - signups@example.com
        action_settings:
            NewClientSignUpAction:
                cloud_tag_id: 1
                non_fiscal_position_countries:
                    - NZ
                fiscal_position_id: 1
            NewProjectSignUpAction:
                default_roles:
                    - project_admin
                    - project_mod
                    - heat_stack_owner
                    - _member_
        default_region: RegionOne
        # If 'None' (null in yaml), will default to domain as parent.
        # If domain isn't set explicity, will use Adjutant's admin user domain.
        default_domain_id: default
        default_parent_id: null
        setup_network: True


Once active, and if debug is turned on, you can see the endpoint and test it
with the browsable django-rest-framework api.

You will also need to add 'adjutant-odoo' plugin settings:

::

    PLUGIN_SETTINGS:
        adjutant-odoo:
            odoorpc:
                odoo:
                    hostname: <odoo_hostname>
                    protocol: jsonrpc+ssl
                    port: 443
                    version: <odoo_version>
                    database: <odoo_db_name>
                    user: <odoo_username
                    password: <odoo_password>
