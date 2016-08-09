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

from odoo_actions.odoo_client import get_odoo_client

from stacktask.actions.models import (
    BaseAction, register_action_class, NewProject)
from serializers import NewClientSignUpSerializer, NewProjectSignUpSerializer


class NewClientSignUp(BaseAction):
    """"""

    required = []

    individual_required = [
        'signup_type',
        'first_name',
        'last_name',
        'email',
        'phone',
        'domain',
        'discount_code',
    ]

    business_required = [
        'signup_type',
        'first_name',
        'last_name',
        'email',
        'phone',
        'domain',
        'company_name',
        'address_1',
        'address_2',
        'city',
        'region',
        'postal_code',
        'country',
        'payment_method',
        'bill_first_name',
        'bill_last_name',
        'bill_email',
        'bill_phone',
        'bill_address_1',
        'bill_address_2',
        'bill_city',
        'bill_region',
        'bill_postal_code',
        'bill_country',
        'discount_code',
    ]

    def __init__(self, data, **kwargs):
        if data['signup_type'] == 'individual':
            self.required = self.individual_required
        else:
            self.required = self.business_required
        super(NewClientSignUp, self).__init__(data, **kwargs)

    def _construct_project_name(self):
        project_name = self.get_cache('project_name')
        if project_name:
            return project_name

        # if domain is present
            # use tld or tldextract to get domain without subdomains
            # make project name
        # else if company name
            # make project name based on companyname.im
        # else
            # make from first+last.im

        # self.set_cache('project_name', project_name)

        return None

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

        self.action.valid = False

    def _pre_approve(self):
        # project_name added to task cache for the follow action
        self.action.task.cache['project_name'] = self._construct_project_name()

        self._validate()
        self.action.save()

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
            self.action.save()
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
            self.action.task.cache['partner_id'] = odoo_resp['partner_id']
            # we also save it to the action cache incase the action runs again
            # both as a flag for completion, and to be able to set it to
            # the task cache again.
            self.set_cache('partner_id', odoo_resp['partner_id'])
        elif self.action.state == "existing":
            try:
                odoo_resp = odoo_client.do_another_odoo_thing()
            except Exception as e:
                self.add_note(
                    "Error: '%s' while setting up partner in Odoo." % e)
                raise

            self.action.task.cache['partner_id'] = odoo_resp['partner_id']
            self.set_cache('partner_id', odoo_resp['partner_id'])

        self.action.save()

    def _submit(self, token_data):
        # mostly there shouldn't need to be anything that occurs here
        # as this action will have completed all it's work at the
        # post_approve step
        pass


class NewProjectSignUp(NewProject):

    # We get rid of project_name as this action
    # will be getting it from the cache.
    required = [
        'username',
        'email',
    ]

    def _validate(self):
        project_name = self.action.task.cache.get('project_name')
        if project_name:
            self.project_name = project_name
            return super(NewProjectSignUp, self)._validate()
        else:
            self.add_note("No project_name has been set.")
            return False

    def _post_approve(self):
        # first we run the inherited _post_approve to create the project
        super(NewProjectSignUp, self)._post_approve()

        if self.get_cache('project_linked'):
            self.add_note("Project already linked in Odoo.")
            return

        # now that the project exists we get the id
        project_id = self.get_cache('project_id')

        try:
            partner_id = self.action.task.cache['partner_id']
            # setup the odoo client
            odoo_client = get_odoo_client()
            odoo_client.do_an_odoo_thing(partner_id, project_id)

            # set a flag to tell us we've linked the project in Odoo.
            self.set_cache('project_linked', True)
        except KeyError:
            self.add_note(
                "Error: No partner id. Failed linking project: %s" %
                self.project_name)
            raise
        except Exception as e:
            self.add_note(
                "Error: '%s' while linking project: %s in Odoo." %
                (e, project_id))
            raise


register_action_class(NewClientSignUp, NewClientSignUpSerializer)
register_action_class(NewProjectSignUp, NewProjectSignUpSerializer)
