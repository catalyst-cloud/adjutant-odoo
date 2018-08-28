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

from rest_framework import status

import mock

from adjutant.api.models import Task, Token
from adjutant.common.tests import fake_clients
from adjutant.common.tests.fake_clients import (
    FakeManager, setup_identity_cache)
from adjutant.common.tests.utils import (
    AdjutantAPITestCase, modify_dict_settings)

from odoo_actions.signup import DEFAULT_PHYSICAL_ADDRESS_CONTACT_NAME
from odoo_actions.tests import odoo_cache, get_odoo_client, setup_odoo_cache


@mock.patch('adjutant.common.user_store.IdentityManager', FakeManager)
@mock.patch('odoo_actions.signup.get_odoo_client', get_odoo_client)
@modify_dict_settings(
    DEFAULT_ACTION_SETTINGS={
        'key_list': ['NewProjectSignUpAction'],
        'operation': 'override',
        'value': {
            'credit_duration': 365,
            'initial_credit_amount': 300.00
         }
    })
class SignupViewTests(AdjutantAPITestCase):

    def setUp(self):
        setup_odoo_cache()

    def test_new_signup(self):
        """
        Ensure the new signup workflow goes as expected.
        """
        setup_identity_cache()

        url = "/v1/openstack/sign-up"

        signup_data = {
            'signup_type': 'organisation',
            'name': 'jim james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'toc_agreed': 'true',
            'company_name': 'Jim-co',
            'address_1': "a street",
            'city': 'some city',
            'postal_code': 'NW1',
            'country': 'NZ',
        }
        response = self.client.post(url, signup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        headers = {
            'project_name': "test_project",
            'project_id': "test_project_id",
            'roles': "admin,_member_",
            'username': "test@example.com",
            'user_id': "test_user_id",
            'authenticated': True,
        }
        new_task = Task.objects.all()[0]
        url = "/v1/tasks/" + new_task.uuid
        data = {"approved": True}
        response = self.client.post(url, data, format='json',
                                    headers=headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {'notes': ['created token']}
        )

        self.assertEquals(len(odoo_cache['partners']), 2)

        odooclient = get_odoo_client()
        search = [
            ('is_company', '=', True),
            ('name', '=', signup_data['company_name'])
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, signup_data['company_name'])

        search = [
            ('is_company', '=', False),
            ('name', '=', signup_data['name'])
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, signup_data['name'])

        search = [
            ('is_company', '=', False),
            ('name', '=', DEFAULT_PHYSICAL_ADDRESS_CONTACT_NAME)
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 0)

        self.assertEquals(len(odoo_cache['projects']), 1)
        self.assertEquals(len(odoo_cache['project_rels']), 3)
        self.assertEquals(len(odoo_cache['credits']), 1)

        self.assertEquals(
            list(odoo_cache['credits'].values())[0]['current_balance'], 300.00)

        new_token = Token.objects.all()[0]
        url = "/v1/tokens/" + new_token.token
        data = {'password': 'testpassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_new_signup_existing_project(self):
        """
        Ensure the new signup workflow goes as expected with
        an existing project (but no existing company).
        """

        project = fake_clients.FakeProject(name="jim-co")

        setup_identity_cache(projects=[project])

        url = "/v1/openstack/sign-up"

        signup_data = {
            'signup_type': 'organisation',
            'name': 'jim james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'toc_agreed': 'true',
            'company_name': 'Jim-co',
            'address_1': "a street",
            'city': 'some city',
            'postal_code': 'NW1',
            'country': 'NZ',
        }
        response = self.client.post(url, signup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        headers = {
            'project_name': "test_project",
            'project_id': "test_project_id",
            'roles': "admin,_member_",
            'username': "test@example.com",
            'user_id': "test_user_id",
            'authenticated': True,
        }
        new_task = Task.objects.all()[0]
        url = "/v1/tasks/" + new_task.uuid
        data = {"approved": True}
        response = self.client.post(url, data, format='json',
                                    headers=headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {'notes': ['created token']}
        )

        self.assertEquals(len(odoo_cache['partners']), 2)

        odooclient = get_odoo_client()
        search = [
            ('is_company', '=', True),
            ('name', '=', signup_data['company_name'])
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, signup_data['company_name'])

        search = [
            ('is_company', '=', False),
            ('name', '=', signup_data['name'])
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, signup_data['name'])

        search = [
            ('is_company', '=', False),
            ('name', '=', DEFAULT_PHYSICAL_ADDRESS_CONTACT_NAME)
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 0)

        self.assertEquals(len(odoo_cache['projects']), 1)
        self.assertEquals(len(odoo_cache['project_rels']), 3)
        self.assertEquals(len(odoo_cache['credits']), 1)

        self.assertEquals(
            list(odoo_cache['credits'].values())[0]['current_balance'], 300.00)

        self.assertEquals(
            len(fake_clients.identity_cache['new_projects']), 1)

        self.assertTrue(
            fake_clients.identity_cache['new_projects'][0].name.startswith(
                project.name))
        self.assertNotEquals(
            fake_clients.identity_cache['new_projects'][0].name,
            project.name)

        new_token = Token.objects.all()[0]
        url = "/v1/tokens/" + new_token.token
        data = {'password': 'testpassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
