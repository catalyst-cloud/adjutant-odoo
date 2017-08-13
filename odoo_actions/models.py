# Copyright (C) 2016 Catalyst IT Ltd
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

from django.utils.text import slugify

from odoo_actions.odoo_client import get_odoo_client
from odoo_actions.utils import generate_short_id

from adjutant.actions.v1.models import register_action_class
from adjutant.actions.v1.base import BaseAction
from adjutant.actions.v1.projects import NewProjectWithUserAction
from adjutant.actions import user_store
from odoo_actions.serializers import (
    NewClientSignUpActionSerializer, NewProjectSignUpActionSerializer)


class NewClientSignUpAction(BaseAction):
    """"""

    required = [
        'signup_type',
        'first_name',
        'last_name',
        'email',
        'phone',
        'discount_code',
        'payment_method',
        'toc_agreed',
    ]

    organisation_required = [
        'signup_type',
        'first_name',
        'last_name',
        'email',
        'phone',
        'company_name',
        'address_1',
        'address_2',
        'city',
        'postal_code',
        'country',
        'payment_method',
        'primary_contact_is_billing',
        'bill_first_name',
        'bill_last_name',
        'bill_email',
        'bill_phone',
        'primary_address_is_billing',
        'bill_address_1',
        'bill_address_2',
        'bill_city',
        'bill_postal_code',
        'bill_country',
        'discount_code',
        'toc_agreed',
    ]

    def __init__(self, data, **kwargs):
        if data['signup_type'] == 'organisation':
            self.required = self.organisation_required

        super(NewClientSignUpAction, self).__init__(data, **kwargs)

        cloud_tag_id = self.settings.get("cloud_tag_id", {})
        if cloud_tag_id:
            self.cloud_tag_id = int(cloud_tag_id)
        else:
            self.cloud_tag_id = None

    # Core action functions:
    def _pre_approve(self):
        # project_name added to task cache for the follow action
        self.action.task.cache['project_name'] = self._construct_project_name()

        self._validate()

    def _post_approve(self):
        self.action.task.cache['project_name'] = self._construct_project_name()

        # revalidate to make sure stuff still makes sense for odoo
        self._validate()
        if not self.valid:
            return

        # now that someone has approved the task this action
        # will need to create data in Odoo based on what the validation
        # found out.
        if self.signup_type == "organisation":
            self._create_organisation()
        elif self.signup_type == "individual":
            self._create_individual()

        # TODO(adriant): Handle discount codes automatically.

    def _submit(self, token_data):
        # mostly there shouldn't need to be anything that occurs here
        # as this action will have completed all it's work at the
        # post_approve step
        pass

    # Helper functions:
    def _construct_project_name(self):
        """Construct Name to match our convention.

        The name needs to be a lowercase slug "[^0-9a-z_-]"
        """
        project_name = self.get_cache('project_name')
        if project_name:
            return project_name

        if self.signup_type == "organisation":
            # TODO(adriant): One option later may be to allow unicode:
            # slugify(value, allow_unicode=True)
            project_name = str(slugify(self.company_name))
        elif self.signup_type == "individual":
            # TODO(adriant): same as above.
            project_name = str(
                slugify("%s-%s" % (self.first_name, self.last_name)))

        # Now lowercase the name and set it to cache
        self.set_cache('project_name', project_name.lower())

        return project_name

    def _validate(self):
        # the serializer validates that the data is present and does some
        # limited formate checking, so now we need to check that the data
        # makes sense for Odoo

        # first we should see if the company or contacts (primary + billing)
        # already exist in Odoo.

        # this function needs to set self.action.valid, and leave notes
        # via self.add_note() for logging the validation.
        # This step is to provide useful info to a human looking at this
        # task to know if they should approve it.

        # to mark if a company/contact/billcontact exists we should use
        # 'self.action.state' or 'self.set_cache(<key>, <value>)'' to set flags
        # for later so this action knows if it should create the new
        # company/contact/etc or not at the post_approve step.

        partner_id = self.get_cache('partner_id')
        if partner_id:
            self.add_note(
                "Skipping validation as we've already created the partner.")
            self.action.valid = True
            self.action.save()
            return

        if self.signup_type == "organisation":
            self.action.valid = (self._validate_organisation() and
                                 self._validate_countries_exists())
        elif self.signup_type == "individual":
            self.action.valid = self._validate_individual()
        self.action.save()

    def _validate_organisation(self):
        odoo_client = get_odoo_client()

        customers = odoo_client.partners.fuzzy_match(
            name=self.company_name, is_company=True)

        if len(customers) > 0:
            for customer in customers:
                if customer['match'] == 1:
                    self.add_note(
                        "Exact company exists: %s" % customer['name'])
                    self._validate_similar_organisation(customer)
                else:
                    self.add_note(
                        "Similar company exists: %s" % customer['name'])
                    self._validate_similar_organisation(customer)

            # We set the name to something obvious in odoo
            self.odoo_company_name = (
                "%s - (POSSIBLE DUPLICATE)" % self.company_name)
            self.add_note(
                "Rather than reuse existing will create duplicate as: '%s'" %
                self.odoo_company_name)
            self.add_note(
                "Needs Manual merge if was correct match, or rename if not.")
            return True
        else:
            self.add_note(
                "No existing company with name '%s'." %
                self.company_name)
            self.odoo_company_name = self.company_name
            return True

    def _validate_similar_organisation(self, customer):
        odoo_client = get_odoo_client()

        company = odoo_client.partners.get(customer['id'])[0]
        tags = [tag.id for tag in company.category_id]
        if self.cloud_tag_id and self.cloud_tag_id in tags:
            self.add_note(
                "Company: %s has cloud tag." % customer['name'])
        elif self.cloud_tag_id:
            self.add_note(
                "Company: %s does not have cloud tag." % customer['name'])

        primary_name = "%s %s" % (self.first_name, self.last_name)
        contacts = odoo_client.partners.fuzzy_match(
            name=primary_name, check_parent=True,
            parent=customer['id'])

        for contact in contacts:
            if contact['match'] == 1:
                self.add_note(
                    "Primary contact: %s found for company: %s" %
                    (contact['name'], customer['name']))
            else:
                self.add_note(
                    "Similar primary contact: %s found for company: %s" %
                    (contact['name'], customer['name']))

        if not self.primary_contact_is_billing:
            billing_name = "%s %s" % (self.first_name, self.last_name)
            contacts = odoo_client.partners.fuzzy_match(
                name=billing_name, check_parent=True,
                parent=customer['id'])

            for contact in contacts:
                if contact['match'] == 1:
                    self.add_note(
                        "Billing contact: %s found for company: %s" %
                        (contact['name'], customer['name']))
                else:
                    self.add_note(
                        "Similar billing contact: %s found for company: %s" %
                        (contact['name'], customer['name']))

    def _validate_individual(self):
        odoo_client = get_odoo_client()

        # TODO(adrian): when odoo supports first/last change this:
        customers = odoo_client.partners.fuzzy_match(
            name="%s %s" % (self.first_name, self.last_name),
            check_parent=True)
        if len(customers) > 0:
            for customer in customers:
                if customer['match'] == 1:
                    self.add_note("Exact customer already exists: %s %s" % (
                        self.first_name, self.last_name))
                else:
                    self.add_note("Similar customer already exists: %s %s" % (
                        self.first_name, self.last_name))

            self.customer_name = ("%s %s - (POSSIBLE DUPLICATE)" % (
                self.first_name, self.last_name))
            self.add_note(
                "Rather than reuse existing will create duplicate as: '%s'" %
                self.customer_name)
            return True
        else:
            self.add_note(
                "No existing customer with name: %s %s" %
                (self.first_name, self.last_name))
            self.customer_name = ("%s %s" % (
                self.first_name, self.last_name))
            return True

    def _validate_countries_exists(self):
        if self.primary_address_is_billing:
            return self._validate_primary_country()

        return (self._validate_primary_country() and
                self._validate_billing_country())

    def _validate_billing_country(self):
        odooclient = get_odoo_client()
        try:
            self.bill_country_id = odooclient.countries.get_closest_country(
                self.bill_country).id
            self.add_note("Found country %s" % self.bill_country)
            return True
        except IndexError:
            self.add_note("Did not find country %s" % self.bill_country)
            return False

    def _validate_primary_country(self):
        odooclient = get_odoo_client()
        try:
            self.country_id = odooclient.countries.get_closest_country(
                self.country).id
            self.add_note("Found country %s" % self.country)
            return True
        except IndexError:
            self.add_note("Did not find country %s" % self.country)
            return False

    def _create_organisation(self):
        odoo_client = get_odoo_client()

        # First we handle the company.
        # In this context partner is the company:
        partner_id = self.get_cache('partner_id')
        if partner_id:
            self.add_note(
                "Partner already created with id: %s." % partner_id)
        else:
            try:
                tags = []
                if self.cloud_tag_id:
                    tags.append((6, 0, [self.cloud_tag_id]))
                partner_id = odoo_client.partners.create(
                    is_company=True, name=self.odoo_company_name,
                    street=self.address_1, street2=self.address_2,
                    city=self.city, zip=self.postal_code,
                    country_id=self.country_id, phone=self.phone,
                    category_id=tags)
            except Exception as e:
                self.add_note(
                    "Error: '%s' while setting up partner in Odoo." % e)
                raise
            self.set_cache('partner_id', partner_id)
            self.add_note("Partner '%s' created." % self.odoo_company_name)
        self.action.task.cache['partner_id'] = partner_id

        # Now we handle the primary contact for the new project:
        primary_id = self.get_cache('primary_id')
        if primary_id:
            self.add_note("Primary contact already created.")
        else:
            try:
                # TODO(adrian): when odoo supports first/last change this:
                name = "%s %s" % (self.first_name, self.last_name)
                if (self.primary_contact_is_billing and
                        not self.primary_address_is_billing):
                    primary_id = odoo_client.partners.create(
                        is_company=False, name=name,
                        street=self.bill_address_1,
                        street2=self.bill_address_2,
                        city=self.bill_city, zip=self.bill_postal_code,
                        country_id=self.bill_country_id,
                        phone=self.bill_phone, parent_id=partner_id)
                else:
                    primary_id = odoo_client.partners.create(
                        is_company=False, name=name,
                        email=self.email, phone=self.phone,
                        parent_id=partner_id,
                        use_parent_address=True)
            except Exception as e:
                self.add_note(
                    "Error: '%s' while setting up "
                    "primary contact in Odoo." % e)
                raise
            self.set_cache('primary_id', primary_id)
            self.add_note("Primary contact '%s' created." % name)
        self.action.task.cache['primary_id'] = primary_id

        billing_id = self.get_cache('billing_id')
        if billing_id:
            self.add_note("Billing contact already created.")
        elif self.primary_contact_is_billing:
            billing_id = primary_id
        elif not self.primary_contact_is_billing:
            try:
                # TODO(adrian): when odoo supports first/last change this:
                name = "%s %s" % (
                    self.bill_first_name, self.bill_last_name)
                if self.primary_address_is_billing:
                    billing_id = odoo_client.partners.create(
                        is_company=False, name=name,
                        email=self.email, phone=self.phone,
                        parent_id=partner_id,
                        use_parent_address=True)
                else:
                    billing_id = odoo_client.partners.create(
                        is_company=False, name=name,
                        street=self.bill_address_1,
                        street2=self.bill_address_2,
                        city=self.bill_city, zip=self.bill_postal_code,
                        country_id=self.bill_country_id,
                        phone=self.bill_phone, parent_id=partner_id)
            except Exception as e:
                self.add_note(
                    "Error: '%s' while setting up "
                    "billing contact in Odoo." % e)
                raise
            self.set_cache('billing_id', billing_id)
            self.add_note("Billing contact '%s' created." % name)
        self.action.task.cache['billing_id'] = billing_id

    def _create_individual(self):
        odoo_client = get_odoo_client()

        partner_id = self.get_cache('partner_id')
        if partner_id:
            self.add_note("Partner already created.")
        else:
            try:
                tags = []
                if self.cloud_tag_id:
                    tags.append((6, 0, [self.cloud_tag_id]))
                partner_id = odoo_client.partners.create(
                    is_company=False, name=self.customer_name,
                    email=self.email, phone=self.phone,
                    category_id=tags)
            except Exception as e:
                self.add_note(
                    "Error: '%s' while setting up partner in Odoo." % e)
                raise
            self.set_cache('partner_id', partner_id)
            self.add_note("Partner '%s' created." % self.customer_name)
        self.action.task.cache['partner_id'] = partner_id


class NewProjectSignUpAction(NewProjectWithUserAction):

    # project_name is not required as this action
    # will be getting it from the cache.
    required = [
        'signup_type',
        'username',
        'email',
        'parent_id',
        'domain_id',
    ]

    def _validate_project_absent(self):
        project_name = self.get_cache('project_name')
        if not project_name:
            project_name = self.action.task.cache.get('project_name')
            if not project_name:
                self.add_note("No project_name has been set.")
                return False

            id_manager = user_store.IdentityManager()

            project = id_manager.find_project(
                project_name, self.domain_id)
            if project:
                self.add_note("Existing project with name '%s'." %
                              project_name)
                self.add_note("Attempting to find unique project name to use.")

                # NOTE(adriant) Mainly to avoid doing a while True loop, or it
                # taking too long.
                name_attempts = 20
                found_new_name = False

                for i in range(name_attempts):
                    ran_hash = generate_short_id()

                    project_name = "%s~%s" % (project_name, ran_hash)
                    project = id_manager.find_project(
                        project_name, self.domain_id)
                    if project:
                        self.add_note(
                            "Existing project with name '%s'." % project_name)
                        continue

                    self.project_name = project_name
                    self.set_cache('project_name', project_name)
                    self.add_note(
                        "No existing project with name '%s'." % project_name)
                    found_new_name = True
                    break

                if not found_new_name:
                    return False
            else:
                self.project_name = project_name
                self.set_cache('project_name', project_name)
                self.add_note(
                    "No existing project with name '%s'." % project_name)

        self.project_name = project_name
        return True

    def _post_approve(self):
        # first we run the inherited _post_approve to create the project
        super(NewProjectSignUpAction, self)._post_approve()

        odoo_project_id = self.get_cache('odoo_project_id')
        contacts_linked = self.get_cache('contacts_linked')

        if odoo_project_id and contacts_linked:
            self.add_note("Project and contacts already linked in Odoo.")
            return

        # now that the project exists we get its id
        project_id = self.get_cache('project_id')

        # update the project with metadata:
        id_manager = user_store.IdentityManager()
        id_manager.update_project(project_id, signup_type=self.signup_type)

        partner_id = self.action.task.cache.get('partner_id')
        if not partner_id:
            self.add_note(
                "Error: No partner_id. Failed linking project: %s" %
                self.project_name)
            self.action.valid = False
            self.action.save()
            return

        if self.signup_type == "organisation":
            primary_id = self.action.task.cache.get('primary_id')
            if not primary_id:
                self.add_note(
                    "Error: No primary_id. Failed linking project: %s" %
                    self.project_name)
                self.action.valid = False
                self.action.save()
                return

        if not odoo_project_id:
            self._create_odoo_project(project_id)

        if not contacts_linked:
            try:
                if self.signup_type == "organisation":
                    self._link_organisation_contacts()
                elif self.signup_type == "individual":
                    self._link_individual()
                self.set_cache('contacts_linked', True)
            except Exception as e:
                self.add_note(
                    "Error: '%s' linking contacts for project: %s in Odoo." %
                    (e, project_id))
                raise

    def _create_odoo_project(self, project_id):
        odoo_client = get_odoo_client()

        try:
            id_manager = user_store.IdentityManager()

            project = id_manager.get_project(project_id)

            odoo_project_id = odoo_client.projects.create(
                name=project.name,
                tenant_id=project.id)

            # set a flag to tell us we've created the project in Odoo.
            self.set_cache('odoo_project_id', odoo_project_id)
        except Exception as e:
            self.add_note(
                "Error: '%s' while linking project: %s in Odoo." %
                (e, project_id))
            raise

    def _link_organisation_contacts(self):
        partner_id = self.action.task.cache.get('partner_id')
        primary_id = self.action.task.cache.get('primary_id')
        odoo_project_id = self.get_cache('odoo_project_id')
        odoo_client = get_odoo_client()

        owner_rel = self.get_cache('owner_rel')
        if not owner_rel:
            owner_rel = odoo_client.project_relationships.create(
                cloud_tenant=odoo_project_id,
                partner_id=partner_id,
                contact_type="owner")
            self.set_cache('owner_rel', owner_rel)

        primary_rel = self.get_cache('primary_rel')
        if not primary_rel:
            primary_rel = odoo_client.project_relationships.create(
                cloud_tenant=odoo_project_id,
                partner_id=primary_id,
                contact_type="primary")
            self.set_cache('primary_rel', primary_rel)

        billing_id = self.action.task.cache.get('billing_id')

        billing_rel = self.get_cache('billing_rel')
        if billing_id and not billing_rel:
            billing_rel = odoo_client.project_relationships.create(
                cloud_tenant=odoo_project_id,
                partner_id=billing_id,
                contact_type="billing")
            self.set_cache('billing_rel', billing_rel)

    def _link_individual(self):
        partner_id = self.action.task.cache.get('partner_id')
        odoo_project_id = self.get_cache('odoo_project_id')
        odoo_client = get_odoo_client()

        owner_rel = self.get_cache('owner_rel')
        if not owner_rel:
            owner_rel = odoo_client.project_relationships.create(
                cloud_tenant=odoo_project_id,
                partner_id=partner_id,
                contact_type="owner")
            self.set_cache('owner_rel', owner_rel)

        primary_rel = self.get_cache('primary_rel')
        if not primary_rel:
            primary_rel = odoo_client.project_relationships.create(
                cloud_tenant=odoo_project_id,
                partner_id=partner_id,
                contact_type="primary")
            self.set_cache('primary_rel', primary_rel)


register_action_class(NewClientSignUpAction, NewClientSignUpActionSerializer)
register_action_class(NewProjectSignUpAction, NewProjectSignUpActionSerializer)
