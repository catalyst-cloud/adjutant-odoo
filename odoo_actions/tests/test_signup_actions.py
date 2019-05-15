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

from adjutant.api.models import Task
from adjutant.common.tests import fake_clients
from adjutant.common.tests.utils import (
     modify_dict_settings, AdjutantTestCase)
from adjutant.common.tests.fake_clients import (
    FakeManager, setup_identity_cache)

from django.test import override_settings

from odoo_actions.tests import (
    odoo_cache, get_odoo_client, setup_odoo_cache, INDIVIDUAL_TAG_ID)
from odoo_actions.signup import (
    NewClientSignUpAction, NewProjectSignUpAction)
from odoo_actions.odoo_client import DEFAULT_PHYSICAL_ADDRESS_CONTACT_NAME


@mock.patch('odoo_actions.odoo_client.get_odoo_client', get_odoo_client)
@override_settings(PLUGIN_SETTINGS={'adjutant-odoo': {
    'fiscal_position_id': 1,
    'cloud_tag_id': 1,
    'non_fiscal_position_countries': ['NZ'],
    'physical_address_contact_name': 'Physical Address',
    'individual_tag_id': INDIVIDUAL_TAG_ID,
    }})
class SignupActionTests(AdjutantTestCase):

    def setUp(self):
        setup_odoo_cache()

    def test_new_customer(self):
        """
        Test the default case, all valid.
        No existing customer. Primary is billing.

        Should create two partners.

        Country NZ, so no fiscal position.
        """
        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={})

        data = {
            'signup_type': 'organisation',
            'name': 'jim james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'stripe_token': '',
            'toc_agreed': 'true',
            'news_agreed': 'true',
            'company_name': 'Jim-co',
            'address_1': "a street",
            'address_2': "",
            'city': 'some city',
            'postal_code': 'NW1',
            'country': 'NZ',
            'primary_contact_is_billing': True,
            'bill_name': '',
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
        self.assertEquals(partners[0].property_account_position, None)

        search = [
            ('is_company', '=', False),
            ('name', '=', data['name'])
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, data['name'])

        search = [
            ('is_company', '=', False),
            ('name', '=', DEFAULT_PHYSICAL_ADDRESS_CONTACT_NAME)
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 0)

        action.submit({})
        self.assertEquals(action.valid, True)

    def test_new_customer_billing_contact(self):
        """
        Test the second default case, all valid.
        No existing customer. Primary is not billing.

        Should create 4 partners.

        Billing address is in AU so fiscal position should be set.
        """
        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={})

        data = {
            'signup_type': 'organisation',
            'name': 'jim james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'stripe_token': '',
            'toc_agreed': 'true',
            'news_agreed': 'true',
            'company_name': 'Jim-co',
            'address_1': "a street",
            'address_2': "",
            'city': 'some city',
            'postal_code': 'NW1',
            'country': 'NZ',
            'primary_contact_is_billing': False,
            'bill_name': 'Oz the Great and Powerful',
            'bill_email': 'oz@em.oz',
            'bill_phone': '123456',
            'primary_address_is_billing': False,
            'bill_address_1': 'yellow brick road',
            'bill_address_2': '',
            'bill_city': 'emerald city',
            'bill_postal_code': 'NW1',
            'bill_country': 'AU',
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
            ('name', '=', data['company_name'])
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, data['company_name'])
        self.assertEquals(partners[0].property_account_position, 1)

        search = [
            ('is_company', '=', False),
            ('name', '=', data['name'])
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, data['name'])

        search = [
            ('is_company', '=', False),
            ('name', '=', data['bill_name'])
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, data['bill_name'])

        search = [
            ('is_company', '=', False),
            ('name', '=', DEFAULT_PHYSICAL_ADDRESS_CONTACT_NAME)
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(
            partners[0].name, DEFAULT_PHYSICAL_ADDRESS_CONTACT_NAME)

        action.submit({})
        self.assertEquals(action.valid, True)

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
            'name': 'jim james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'stripe_token': '',
            'toc_agreed': 'true',
            'news_agreed': 'true',
            'company_name': 'Jim-co',
            'address_1': "a street",
            'address_2': "",
            'city': 'some city',
            'postal_code': 'NW1',
            'country': 'NZ',
            'primary_contact_is_billing': True,
            'bill_name': '',
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

        search = [
            ('is_company', '=', False),
            ('name', '=', data['name'])
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 2)
        self.assertEquals(partners[0].name, data['name'])
        self.assertEquals(partners[1].name, data['name'])

        search = [
            ('is_company', '=', False),
            ('name', '=', DEFAULT_PHYSICAL_ADDRESS_CONTACT_NAME)
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 0)

        action.submit({})
        self.assertEquals(action.valid, True)

    def test_new_customer_individual(self):
        """
        Test individual.
        No existing customer.

        Should create 2 partners.

        Fiscal position is not set because in NZ.
        """
        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={})

        data = {
            'signup_type': 'individual',
            'name': 'jim james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'stripe_token': '',
            'toc_agreed': 'true',
            'news_agreed': 'true',
            'bill_address_1': 'yellow brick road',
            'bill_address_2': '',
            'bill_city': 'emerald city',
            'bill_postal_code': 'NW1',
            'bill_country': 'NZ',
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
            ('name', '=', data['name'])
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, data['name'])
        self.assertEquals(partners[0].country_id.id, 3)
        self.assertEquals(partners[0].property_account_position, None)

        action.submit({})
        self.assertEquals(action.valid, True)

    def test_new_customer_individual_false_duplicate(self):
        """
        Test individual.
        Existing customer with 'contact' that matches name.

        Should not flag non_company contact as a possible match.

        Should create 2 partner.
        """

        odooclient = get_odoo_client()
        existing_company_id = odooclient.partners.create(
            name="test company", is_company=True)
        odooclient.partners.create(
            name="jim james", parent_id=existing_company_id)

        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={})

        data = {
            'signup_type': 'individual',
            'name': 'jim james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'stripe_token': '',
            'toc_agreed': 'true',
            'news_agreed': 'true',
            'bill_address_1': 'yellow brick road',
            'bill_address_2': '',
            'bill_city': 'emerald city',
            'bill_postal_code': 'NW1',
            'bill_country': 'NZ',
            'discount_code': '',
        }

        action = NewClientSignUpAction(data, task=task, order=1)

        action.pre_approve()
        self.assertEquals(action.valid, True)
        self.assertNotIn("(POSSIBLE DUPLICATE)", action.customer_name)

        action.post_approve()
        self.assertEquals(action.valid, True)
        self.assertEquals(len(odoo_cache['partners']), 4)

        search = [
            ('is_company', '=', True),
            ('name', '=', data['name'])
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, data['name'])
        self.assertEquals(partners[0].country_id.id, 3)
        self.assertEquals(partners[0].property_account_position, None)

        action.submit({})
        self.assertEquals(action.valid, True)

    def test_new_customer_individual_fiscal_position(self):
        """
        Test individual.
        No existing customer.

        Should create 2 partners.

        Fiscal position is set because not in NZ.
        """
        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={})

        data = {
            'signup_type': 'individual',
            'name': 'jim james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'stripe_token': '',
            'toc_agreed': 'true',
            'news_agreed': 'true',
            'bill_address_1': 'yellow brick road',
            'bill_address_2': '',
            'bill_city': 'emerald city',
            'bill_postal_code': 'NW1',
            'bill_country': 'AU',
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
            ('name', '=', data['name'])
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, data['name'])
        self.assertEquals(partners[0].country_id.id, 4)
        self.assertEquals(partners[0].property_account_position, 1)

        action.submit({})
        self.assertEquals(action.valid, True)


@mock.patch('adjutant.common.user_store.IdentityManager', FakeManager)
@mock.patch('odoo_actions.odoo_client.get_odoo_client', get_odoo_client)
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

    def test_new_project_signup(self):
        """
        Base case, no project, no user.

        Organisation, and primary is billing.

        Project and user created at post_approve step,
        user password at submit step.
        """

        setup_identity_cache()

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
            fake_clients.identity_cache['new_projects'][0].name,
            'test_project')

        token_data = {'password': '123456'}
        action.submit(token_data)
        self.assertEquals(action.valid, True)

        new_project = fake_clients.identity_cache['new_projects'][0]
        new_user = fake_clients.identity_cache['new_users'][0]
        self.assertEquals(new_user.email, 'test@example.com')
        fake_client = fake_clients.FakeManager()
        roles = fake_client._get_roles_as_names(new_user, new_project)
        self.assertEquals(
            sorted(roles),
            sorted(['_member_', 'project_admin',
                    'project_mod', 'heat_stack_owner']))

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

        project = fake_clients.FakeProject(name="test_project")

        setup_identity_cache(projects=[project])

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
            len(fake_clients.identity_cache['new_projects']), 1)
        self.assertNotEquals(
            action.project_name, 'test_project')

        token_data = {'password': '123456'}
        action.submit(token_data)
        self.assertEquals(action.valid, True)

        new_project = fake_clients.identity_cache['new_projects'][0]
        new_user = fake_clients.identity_cache['new_users'][0]
        self.assertEquals(new_user.email, 'test@example.com')
        fake_client = fake_clients.FakeManager()
        roles = fake_client._get_roles_as_names(new_user, new_project)
        self.assertEquals(
            sorted(roles),
            sorted(['_member_', 'project_admin',
                    'project_mod', 'heat_stack_owner']))
