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

import mock

from odoo_actions.models import (
    NewClientSignUpAction, NewProjectSignUpAction)
from adjutant.api.models import Task
from adjutant.api.v1 import tests
from adjutant.api.v1.tests import (
    FakeManager, setup_temp_cache, modify_dict_settings, AdjutantTestCase)

from odoo_actions.tests import odoo_cache, get_odoo_client, setup_odoo_cache


class SignupActionTests(AdjutantTestCase):

    def setUp(self):
        setup_odoo_cache()

    @mock.patch('odoo_actions.models.get_odoo_client',
                get_odoo_client)
    def test_new_customer(self):
        """
        Test the default case, all valid.
        No existing customer. Primary is billing.

        Should create two partners.
        """
        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={})

        data = {
            'signup_type': 'organisation',
            'first_name': 'jim',
            'last_name': 'james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'toc_agreed': 'true',
            'company_name': 'Jim-co',
            'address_1': "a street",
            'address_2': "",
            'city': 'some city',
            'postal_code': 'NW1',
            'country': 'nz',
            'primary_contact_is_billing': True,
            'bill_first_name': '',
            'bill_last_name': '',
            'bill_email': '',
            'bill_phone': '',
            'primary_address_is_billing': True,
            'bill_address_1': '',
            'bill_address_2': '',
            'bill_city': '',
            'bill_postal_code': '',
            'bill_country': '',
            'discount_code': '',
        }

        action = NewClientSignUpAction(data, task=task, order=1)

        action.pre_approve()
        self.assertEquals(action.valid, True)

        action.post_approve()
        self.assertEquals(action.valid, True)
        self.assertEquals(len(odoo_cache['partners']), 2)

        odooclient = get_odoo_client()
        search = [
            ('is_company', '=', True),
            ('name', '=', data['company_name'])
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, data['company_name'])

        primary_name = "%s %s" % (data['first_name'], data['last_name'])
        odooclient = get_odoo_client()
        search = [
            ('is_company', '=', False),
            ('name', '=', primary_name)
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, primary_name)

        action.submit({})
        self.assertEquals(action.valid, True)

    @mock.patch('odoo_actions.models.get_odoo_client',
                get_odoo_client)
    def test_new_customer_billing_contact(self):
        """
        Test the second default case, all valid.
        No existing customer. Primary is not billing.

        Should create 3 partners.
        """
        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={})

        data = {
            'signup_type': 'organisation',
            'first_name': 'jim',
            'last_name': 'james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'toc_agreed': 'true',
            'company_name': 'Jim-co',
            'address_1': "a street",
            'address_2': "",
            'city': 'some city',
            'postal_code': 'NW1',
            'country': 'nz',
            'primary_contact_is_billing': False,
            'bill_first_name': 'Oz',
            'bill_last_name': 'Great and Powerful',
            'bill_email': 'oz@em.oz',
            'bill_phone': '123456',
            'primary_address_is_billing': False,
            'bill_address_1': 'yellow brick road',
            'bill_address_2': '',
            'bill_city': 'emerald city',
            'bill_postal_code': 'NW1',
            'bill_country': 'Oz',
            'discount_code': '',
        }

        action = NewClientSignUpAction(data, task=task, order=1)

        action.pre_approve()
        self.assertEquals(action.valid, True)

        action.post_approve()
        self.assertEquals(action.valid, True)
        self.assertEquals(len(odoo_cache['partners']), 3)

        odooclient = get_odoo_client()
        search = [
            ('is_company', '=', True),
            ('name', '=', data['company_name'])
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, data['company_name'])

        primary_name = "%s %s" % (data['first_name'], data['last_name'])
        odooclient = get_odoo_client()
        search = [
            ('is_company', '=', False),
            ('name', '=', primary_name)
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, primary_name)

        billing_name = "%s %s" % (
            data['bill_first_name'], data['bill_last_name'])
        odooclient = get_odoo_client()
        search = [
            ('is_company', '=', False),
            ('name', '=', billing_name)
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, billing_name)

        action.submit({})
        self.assertEquals(action.valid, True)

    @mock.patch('odoo_actions.models.get_odoo_client',
                get_odoo_client)
    def test_new_customer_duplicate(self):
        """
        Test the duplicate case, all valid.
        Existing customer. Primary is billing.

        Should create two partners, the company with
        "POSSIBLE DUPLICATE" in the name.
        """

        # First we will use another test to setup
        # an existing customer.
        self.test_new_customer()

        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={})

        data = {
            'signup_type': 'organisation',
            'first_name': 'jim',
            'last_name': 'james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'toc_agreed': 'true',
            'company_name': 'Jim-co',
            'address_1': "a street",
            'address_2': "",
            'city': 'some city',
            'postal_code': 'NW1',
            'country': 'nz',
            'primary_contact_is_billing': True,
            'bill_first_name': '',
            'bill_last_name': '',
            'bill_email': '',
            'bill_phone': '',
            'primary_address_is_billing': True,
            'bill_address_1': '',
            'bill_address_2': '',
            'bill_city': '',
            'bill_postal_code': '',
            'bill_country': '',
            'discount_code': '',
        }

        action = NewClientSignUpAction(data, task=task, order=1)

        action.pre_approve()
        self.assertEquals(action.valid, True)

        action.post_approve()
        self.assertEquals(action.valid, True)
        self.assertEquals(len(odoo_cache['partners']), 4)

        odooclient = get_odoo_client()
        search = [
            ('is_company', '=', True),
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 2)
        self.assertTrue(
            '(POSSIBLE DUPLICATE)' in partners[0].name or
            '(POSSIBLE DUPLICATE)' in partners[1].name)

        primary_name = "%s %s" % (data['first_name'], data['last_name'])
        odooclient = get_odoo_client()
        search = [
            ('is_company', '=', False),
            ('name', '=', primary_name)
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 2)
        self.assertEquals(partners[0].name, primary_name)
        self.assertEquals(partners[1].name, primary_name)

        action.submit({})
        self.assertEquals(action.valid, True)


@modify_dict_settings(
    DEFAULT_ACTION_SETTINGS={
        'key_list': ['NewProjectSignUpAction'],
        'operation': 'override',
        'value': {
            "default_roles": [
                "project_admin",
                "project_mod",
                "heat_stack_owner",
                "_member_",
            ]
         }
    })
class NewProjectSignUpActionTests(AdjutantTestCase):

    def setUp(self):
        setup_odoo_cache()

    @mock.patch('adjutant.actions.user_store.IdentityManager',
                FakeManager)
    @mock.patch('odoo_actions.models.get_odoo_client',
                get_odoo_client)
    def test_new_project_signup(self):
        """
        Base case, no project, no user.

        Organisation, and primary is billing.

        Project and user created at post_approve step,
        user password at submit step.
        """

        setup_temp_cache({}, {})

        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={}
        )

        task.cache = {
            'project_name': 'test_project',
            'partner_id': 1,
            'primary_id': 2,
            'billing_id': 2,
        }

        data = {
            'domain_id': 'default',
            'parent_id': None,
            'email': 'test@example.com',
            'signup_type': 'organisation',
        }

        action = NewProjectSignUpAction(data, task=task, order=1)

        action.pre_approve()
        self.assertEquals(action.valid, True)

        action.post_approve()

        self.assertEquals(len(odoo_cache['projects']), 1)
        self.assertEquals(len(odoo_cache['project_rels']), 3)

        self.assertEquals(action.valid, True)
        self.assertEquals(
            tests.temp_cache['projects']['test_project'].name,
            'test_project')

        token_data = {'password': '123456'}
        action.submit(token_data)
        self.assertEquals(action.valid, True)
        self.assertEquals(
            tests.temp_cache['users']["user_id_1"].email,
            'test@example.com')
        project = tests.temp_cache['projects']['test_project']
        self.assertEquals(
            sorted(project.roles["user_id_1"]),
            sorted(['_member_', 'project_admin',
                    'project_mod', 'heat_stack_owner']))

    @mock.patch('adjutant.actions.user_store.IdentityManager',
                FakeManager)
    @mock.patch('odoo_actions.models.get_odoo_client',
                get_odoo_client)
    def test_new_project_signup_existing(self):
        """
        Existing project case, existing project, no user.

        Organisation, and primary is billing.

        Project and user created at post_approve step,
        user password at submit step.

        The only difference here to the default case
        is that we find/create a new unique project name
        and thus avoid the conflict entirely.
        """

        project = mock.Mock()
        project.id = 'test_project_id'
        project.name = 'test_project'
        project.domain = 'default'
        project.roles = {}

        setup_temp_cache({project.name: project}, {})

        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={}
        )

        task.cache = {
            'project_name': 'test_project',
            'partner_id': 1,
            'primary_id': 2,
            'billing_id': 2,
        }

        data = {
            'domain_id': 'default',
            'parent_id': None,
            'email': 'test@example.com',
            'signup_type': 'organisation',
        }

        action = NewProjectSignUpAction(data, task=task, order=1)

        action.pre_approve()
        self.assertEquals(action.valid, True)

        action.post_approve()

        self.assertEquals(len(odoo_cache['projects']), 1)
        self.assertEquals(len(odoo_cache['project_rels']), 3)

        self.assertEquals(action.valid, True)
        self.assertEquals(
            len(tests.temp_cache['projects']), 2)
        self.assertNotEquals(
            action.project_name, 'test_project')

        token_data = {'password': '123456'}
        action.submit(token_data)
        self.assertEquals(action.valid, True)
        self.assertEquals(
            tests.temp_cache['users']["user_id_1"].email,
            'test@example.com')
        project = tests.temp_cache['projects'][action.project_name]
        self.assertEquals(
            sorted(project.roles["user_id_1"]),
            sorted(['_member_', 'project_admin',
                    'project_mod', 'heat_stack_owner']))
