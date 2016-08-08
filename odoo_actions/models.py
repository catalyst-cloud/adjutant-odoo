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
        # serializer has validated the data content, so we need to check
        # now that the data makes sense for Odoo

        # first we should see if the company or contacts (primary + billing)
        # already exist in Odoo.

        # this function needs to set self.action.valid, and leave notes
        # via self.add_note() for logging the validation.
        # This step is to provide useful info to a human looking at this
        # task to know if they should approve it.

        # to mark if a company/contact/billcontact exists we should use
        # self.set_cache(<key>, <value>) to set flags for later
        # so this action knows if it should create the new company/contact/etc
        # or not at the post_approve step.

        self.action.valid = False

    def _pre_approve(self):
        # project_name added to task cache for the follow action
        self.action.task.cache['project_name'] = self._construct_project_name()

        self._validate()
        self.action.save()

    def _post_approve(self):
        self.action.task.cache['project_name'] = self._construct_project_name()

        # revalidate to make sure stuff still makes sense for odoo
        self._validate()

        # now that someone has approved the task this action
        # will need to create data in Odoo based on what the validation
        # found out.

        odoo_client = get_odoo_client()

        if self.get_cache("should_i?"):
            odoo_client.do_an_odoo_thing()
        else:
            odoo_client.do_another_odoo_thing()

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


register_action_class(NewClientSignUp, NewClientSignUpSerializer)
register_action_class(NewProjectSignUp, NewProjectSignUpSerializer)
