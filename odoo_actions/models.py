# Copyright (C) 2015 Catalyst IT Ltd
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

from stacktask.actions.models import BaseAction, register_action_class
# from serializers import NewOdooClientSerializer, NewOdooContactSerializer


class NewOdooClient(BaseAction):
    """"""

    required = [
        'business_name',
        'billing_address',
        'billing_phone',
        'billing_email'
    ]

    def _pre_approve(self):
        self.action.valid = True
        self.action.need_token = False
        self.action.save()
        return []

    def _post_approve(self):
        self.action.valid = True
        self.action.need_token = False
        self.action.save()
        return []

    def _submit(self, token_data):
        pass


class NewOdooContact(BaseAction):
    """"""

    required = [
        'email'
    ]

    def _pre_approve(self):
        self.action.valid = True
        self.action.need_token = False
        self.action.save()
        return []

    def _post_approve(self):
        self.action.valid = True
        self.action.need_token = False
        self.action.save()
        return []

    def _submit(self, token_data):
        pass


register_action_class(NewOdooClient, None)
register_action_class(NewOdooContact, None)
