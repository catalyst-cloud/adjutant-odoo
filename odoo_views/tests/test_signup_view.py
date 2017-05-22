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

from rest_framework.test import APITestCase

from rest_framework import status

import mock

from adjutant.api.models import Task, Token
from adjutant.api.v1 import tests
from adjutant.api.v1.tests import FakeManager, setup_temp_cache

from odoo_actions.tests import odoo_cache, get_odoo_client, setup_odoo_cache


class SignupViewTests(APITestCase):

    def setUp(self):
        setup_odoo_cache()

    @mock.patch('adjutant.actions.user_store.IdentityManager',
                FakeManager)
    @mock.patch('odoo_actions.models.get_odoo_client',
                get_odoo_client)
    def test_new_signup(self):
        """
        Ensure the new signup workflow goes as expected.
        """
        setup_temp_cache({}, {})

        url = "/v1/openstack/sign-up"

        signup_data = {
            'signup_type': 'organisation',
            'first_name': 'jim',
            'last_name': 'james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'toc_agreed': 'true',
            'company_name': 'Jim-co',
            'address_1': "a street",
            'city': 'some city',
            'postal_code': 'NW1',
            'country': 'nz',
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

        primary_name = "%s %s" % (
            signup_data['first_name'], signup_data['last_name'])
        odooclient = get_odoo_client()
        search = [
            ('is_company', '=', False),
            ('name', '=', primary_name)
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, primary_name)

        self.assertEquals(len(odoo_cache['projects']), 1)
        self.assertEquals(len(odoo_cache['project_rels']), 3)

        new_token = Token.objects.all()[0]
        url = "/v1/tokens/" + new_token.token
        data = {'password': 'testpassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch('adjutant.actions.user_store.IdentityManager',
                FakeManager)
    @mock.patch('odoo_actions.models.get_odoo_client',
                get_odoo_client)
    def test_new_signup_existing_project(self):
        """
        Ensure the new signup workflow goes as expected with
        and existing project (but no existing company).
        """

        project = mock.Mock()
        project.id = 'test_project_id'
        project.name = 'test_project'
        project.domain = 'default'
        project.roles = {}

        setup_temp_cache({project.name: project}, {})

        url = "/v1/openstack/sign-up"

        signup_data = {
            'signup_type': 'organisation',
            'first_name': 'jim',
            'last_name': 'james',
            'email': 'jim@jim.jim',
            'phone': '123456',
            'payment_method': 'invoice',
            'toc_agreed': 'true',
            'company_name': 'Jim-co',
            'address_1': "a street",
            'city': 'some city',
            'postal_code': 'NW1',
            'country': 'nz',
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

        primary_name = "%s %s" % (
            signup_data['first_name'], signup_data['last_name'])
        odooclient = get_odoo_client()
        search = [
            ('is_company', '=', False),
            ('name', '=', primary_name)
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].name, primary_name)

        self.assertEquals(len(odoo_cache['projects']), 1)
        self.assertEquals(len(odoo_cache['project_rels']), 3)

        self.assertEquals(len(tests.temp_cache['projects']), 2)

        new_token = Token.objects.all()[0]
        url = "/v1/tokens/" + new_token.token
        data = {'password': 'testpassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
