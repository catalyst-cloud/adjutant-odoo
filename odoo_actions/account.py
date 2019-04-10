# Copyright (C) 2018 Catalyst IT Ltd
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.conf import settings

from adjutant.actions.v1.base import BaseAction, ResourceMixin
from adjutant.actions.utils import validate_steps
from adjutant.common import user_store

from odoo_actions import odoo_client
from odoo_actions.base import OdooMixin


class UpdateAccountDetailsAction(BaseAction, ResourceMixin, OdooMixin):
    required = [
        'project_id',
        'name',
        'address_1',
        'address_2',
        'city',
        'postal_code',
        'country'
    ]

    def __init__(self, data, **kwargs):
        super(UpdateAccountDetailsAction, self).__init__(data, **kwargs)
        odoo_settings = settings.PLUGIN_SETTINGS.get(
            'adjutant-odoo', {})

        self.non_fiscal_position_countries = odoo_settings.get(
            "non_fiscal_position_countries", ['NZ'])
        self.fiscal_position_id = odoo_settings.get("fiscal_position_id", None)
        if self.fiscal_position_id:
            self.fiscal_position_id = int(self.fiscal_position_id)

    def _check_fiscal_position(self):
        """Check if we need to set a fiscal position.

        Expects:
            - self.country
            - self.non_fiscal_position_countries
        """
        if self.country not in self.non_fiscal_position_countries:
            self.add_note(
                "Will set fiscal position for customer from %s"
                % self.country)
            return True
        return False

    def _update_partner(self, partner):
        """Update the name and address fields on the given partner

        Expects:
            - self.name
            - self.address_1
            - self.address_2
            - self.city
            - self.postal_code
            - self.country_id
        """
        odooclient = odoo_client.get_odoo_client()

        name_changed = partner.name != self.name

        address_changed = any([
            partner.street != self.address_1,
            partner.street2 != self.address_2,
            partner.city != self.city,
            partner.zip != self.postal_code,
            partner.country_id != self.country_id,
        ])

        message_str = ""

        if name_changed:
            message_str += (
                "<dt>Partner has changed their name from:</dt>"
                "<dd>%s</dd><dt>to</dt><dd>%s</dd>" %
                (partner.name, self.name))

        if address_changed:
            message_str += (
                "<dt>Partner address has changed. Prior address was: </dt>"
                "<dd>%s</dd><dd>%s</dd><dd>%s, %s</dd><dd>%s</dd>" % (
                    partner.street, partner.street2,
                    partner.city, partner.zip,
                    partner.country_id.name))

        odooclient.partners.add_internal_note(partner.id, message_str)

        # Turn auto_commit off briefy to increase speed
        odooclient._odoorpc.config['auto_commit'] = False
        partner.name = self.name
        partner.street = self.address_1
        partner.street2 = self.address_2
        partner.city = self.city
        partner.zip = self.postal_code
        partner.country_id = self.country_id

        self.add_note("Updated address of partner '%s'" % partner.name)
        partner.env.commit()

        odooclient._odoorpc.config['auto_commit'] = True

    def _update_fiscal_position(self, partner):
        """Update fiscal position on partner

        Expects:
            - self.country_change
            - self.fiscal_position_id
        """
        if self.country_change:
            if self._check_fiscal_position():
                if self.fiscal_position_id:
                    self.add_note("Setting fiscal position")
                    partner.property_account_position = \
                        self.fiscal_position_id
                else:
                    self.add_note("Fiscal position tag not defined")
            else:
                self.add_note("Fiscal position now set to false.")
                partner.property_account_position = False

    # TODO(adriant): make sure the API GET returns if is root project so
    # the gui can hide the edit buttom
    def _validate_is_root_project(self):
        """Ensure project is root

        We can't let a non root project be edited. User should always
        be scoped to root project to edit the address.

        Expects:
            - self.project_id
        """
        id_manager = user_store.IdentityManager()
        project = id_manager.get_project(self.project_id)
        if project.parent_id:
            parent = id_manager.get_project(project.parent_id)
            if not parent.is_domain:
                self.add_note('Project with id %s is not a root project.' %
                              self.project_id)
                return False
        return True

    def _validate_no_change_in_country(self):
        """Check if there is a change in country

        Expects:
            - self.odoo_owner
            - self.country_id
        Sets:
            - self.country_change
        """
        self._get_parent_id()

        initial_country = self.odoo_owner.country_id

        if self.country_id.id != initial_country.id:
            self.add_note(
                "Country switching from %s to %s. Approval required" %
                (initial_country.name, self.country_id.name))
            self.set_auto_approve(False)
            self.country_change = True
        else:
            self.set_auto_approve(True)
            self.country_change = False

        # A change in country will require approval, but is still valid
        return True

    def _validate_country_exists(self):
        """
        Takes a country name (self.country) and attempts to find a
        fuzzy match for it (self.country_id)

        Expects:
            - self.country
        Sets:
            - self.country_id
        """
        odooclient = odoo_client.get_odoo_client()
        try:
            self.country_id = odooclient.countries.get_closest_country(
                self.country)
            self.add_note("Found country %s" % self.country_id.name)
            return True
        except IndexError:
            self.add_note("Did not find country %s" % self.country)
            return False

    def _validate(self):
        self.action.valid = validate_steps([
            self._validate_project_id,
            self._validate_project_exists,
            self._validate_is_root_project,
            self._validate_country_exists,
            self._validate_no_change_in_country,
        ])

        self.action.save()

    def pre_approve(self):
        # Validation steps
        self._validate()

    def post_approve(self):
        self._validate()
        if self.action.valid:
            self.add_note("Updating billing address")
            address_contact = self.odoo_owner
            self._update_partner(address_contact)
            self._update_fiscal_position(address_contact)

    def submit(self, data):
        # Nothing to do here, all done at post_approve
        pass
