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

import re

from odoo_actions.odoo_client import get_odoo_client
from odoo_actions.utils import generate_short_id

from stacktask.actions.models import (
    BaseAction, register_action_class, NewProjectWithUser)
from stacktask.actions import user_store
from odoo_actions.serializers import (
    NewClientSignUpSerializer, NewProjectSignUpSerializer)


class NewClientSignUp(BaseAction):
    """"""

    required = [
        'signup_type',
        'first_name',
        'last_name',
        'email',
        'phone',
        'discount_code',
        'payment_method',
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
        'region',
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
        'bill_region',
        'bill_postal_code',
        'bill_country',
        'discount_code',
    ]

    def __init__(self, data, **kwargs):
        if data['signup_type'] == 'organisation':
            self.required = self.organisation_required
        super(NewClientSignUp, self).__init__(data, **kwargs)

    def _construct_project_name(self):
        project_name = self.get_cache('project_name')
        if project_name:
            return project_name

        if self.signup_type == "organisation":
            # TODO(adriant): Figure out better regex as these may be
            # too restrictive.
            regex = re.compile('[^0-9a-zA-Z._-]')
            project_name = regex.sub('', self.company_name.replace(' ', '-'))
        elif self.signup_type == "individual":
            # TODO(adriant): same as above.
            regex = re.compile('[^a-zA-Z]')
            project_name = "%s-%s" % (
                regex.sub('', self.first_name.replace(' ', '-')),
                regex.sub('', self.last_name.replace(' ', '-')))

        self.set_cache('project_name', project_name)

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

        self.action.valid = True
        self.action.save()

    def _pre_approve(self):
        # project_name added to task cache for the follow action
        self.action.task.cache['project_name'] = self._construct_project_name()

        self._validate()

    def _post_approve(self):
        self.action.task.cache['project_name'] = self._construct_project_name()

        partner_id = self.get_cache('partner_id')
        if partner_id:
            self.action.task.cache['partner_id'] = partner_id
            self.add_note("Partner already created.")
            return

        # revalidate to make sure stuff still makes sense for odoo
        self._validate()
        if not self.valid:
            return

        # now that someone has approved the task this action
        # will need to create data in Odoo based on what the validation
        # found out.

        odoo_client = get_odoo_client()

        if self.action.state == 'default':
            try:
                odoo_resp = odoo_client.do_an_odoo_thing()
            except Exception as e:
                self.add_note(
                    "Error: '%s' while setting up partner in Odoo." % e)
                raise

            # we need to set the partner_id to the task cache
            # so it can be used by the NewProject _post_approve
            # step
            self.action.task.cache['partner_id'] = odoo_resp.get('partner_id')
            # we also save it to the action cache incase the action runs again
            # both as a flag for completion, and to be able to set it to
            # the task cache again.
            self.set_cache('partner_id', odoo_resp.get('partner_id'))
        elif self.action.state == "existing":
            try:
                odoo_resp = odoo_client.do_an_odoo_thing()
            except Exception as e:
                self.add_note(
                    "Error: '%s' while setting up partner in Odoo." % e)
                raise

            self.action.task.cache['partner_id'] = odoo_resp.get('partner_id')
            self.set_cache('partner_id', odoo_resp.get('partner_id'))

        self.action.save()

    def _submit(self, token_data):
        # mostly there shouldn't need to be anything that occurs here
        # as this action will have completed all it's work at the
        # post_approve step
        pass


class NewProjectSignUp(NewProjectWithUser):

    # We get rid of project_name as this action
    # will be getting it from the cache.
    required = [
        'signup_type',
        'username',
        'email',
        'parent_id',
        'domain_id',
    ]

    def _validate_project(self):
        id_manager = user_store.IdentityManager()

        domain = id_manager.get_domain(self.domain_id)
        if not domain:
            self.add_note('Domain does not exist.')
            return False

        # NOTE(adriant): If parent id is None, Keystone defaults to the domain.
        # So we only care to validate if parent_id is not None.
        if self.parent_id:
            parent = id_manager.get_project(self.parent_id)
            if not parent:
                self.add_note("Parent id: '%s' not for an existing project." %
                              self.project_name)
                return False

        project_name = self.get_cache('project_name')
        if not project_name:
            project_name = self.action.task.cache.get('project_name')
            if not project_name:
                self.add_note("No project_name has been set.")
                return False

            project = id_manager.find_project(project_name, self.domain_id)
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
        super(NewProjectSignUp, self)._post_approve()

        project_linked = self.get_cache('project_linked')
        user_linked = self.get_cache('user_linked')

        if project_linked and user_linked:
            self.add_note("Project and user already linked in Odoo.")
            return

        # now that the project and user exist we get their ids
        project_id = self.get_cache('project_id')
        user_id = self.get_cache('user_id')

        # update the project with metadata:
        id_manager = user_store.IdentityManager()
        id_manager.update_project(project_id, signup_type=self.signup_type)

        try:
            partner_id = self.action.task.cache['partner_id']
            # setup the odoo client
            odoo_client = get_odoo_client()
        except KeyError:
            self.add_note(
                "Error: No partner id. Failed linking project: %s" %
                self.project_name)
            raise
        except Exception as e:
            self.add_note(
                "Error: '%s' while setting up Odooclient." % e)
            raise

        if not project_linked:
            try:
                odoo_client.do_another_odoo_thing(partner_id, project_id)

                # set a flag to tell us we've linked the project in Odoo.
                self.set_cache('project_linked', True)
            except Exception as e:
                self.add_note(
                    "Error: '%s' while linking project: %s in Odoo." %
                    (e, project_id))
                raise

        if not user_linked:
            try:
                odoo_client.do_another_odoo_thing(partner_id, user_id)

                # set a flag to tell us we've linked the user in Odoo.
                self.set_cache('user_linked', True)
            except Exception as e:
                self.add_note(
                    "Error: '%s' while linking user: %s in Odoo." %
                    (e, user_id))
                raise


register_action_class(NewClientSignUp, NewClientSignUpSerializer)
register_action_class(NewProjectSignUp, NewProjectSignUpSerializer)
