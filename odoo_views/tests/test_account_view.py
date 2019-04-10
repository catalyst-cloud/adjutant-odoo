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
from django.test.utils import override_settings

from rest_framework import status

import mock

from adjutant.api.models import Task
from adjutant.common.tests import fake_clients

from odoo_actions.tests import (odoo_cache, get_odoo_client, setup_odoo_cache,
                                OdooObject)


@mock.patch('adjutant.common.user_store.IdentityManager',
            fake_clients.FakeManager)
@mock.patch('odoo_actions.odoo_client.get_odoo_client', get_odoo_client)
@override_settings(PLUGIN_SETTINGS={'adjutant-odoo': {
    'fiscal_position_id': 1,
    'non_fiscal_position_countries': ['NZ'],
}})
class AccountViewTests(APITestCase):

    def setUp(self):
        setup_odoo_cache()

        self.project = fake_clients.FakeProject(
            name='Company Cloud Project')
        fake_clients.setup_identity_cache(projects=[self.project])

        odoo_cache['partners'] = {
            1: {
                'display_name': "The Company, Davey",
                'name': 'Davey',
                'email': "davey@company.com",
                'phone': "555-555-555",
                'id': 1,
                'country_id': 3,
                'parent_id': 3,
                'is_company': False,
            },
            2: {
                'display_name': "The Company, billing",
                'name': 'billing',
                'email': 'billing@company.com',
                'phone': False,
                'id': 2,
                'country_id': 3,
                'parent_id': 3,
                'is_company': False,
            },
            3: {
                'display_name': 'The Company',
                'name': 'The Company',
                'email': 'important@company.com',
                'phone': '555-555-555',
                'id': 3,
                'country_id': 3,
                'is_company': True,
                'street': 'a road',
                'street2': False,
                'zip': '90210',
                'city': 'Wellington',
                'property_account_position': False,
                'category_id': [],
            }}

        odoo_cache['projects'] = {
            1: {'name': self.project.name,
                'tenant_id': self.project.id,
                'id': 1,
                'po_number': "Sale01"
                }}

        odoo_cache['project_rels'] = {
            12: {'contact_type': 'owner',
                 'partner_id': OdooObject(odoo_cache['partners'][3]),
                 'cloud_tenant': 1, 'id': 12},
            13: {'contact_type': 'billing',
                 'partner_id': OdooObject(odoo_cache['partners'][2]),
                 'cloud_tenant': 1, 'id': 13, },
            16: {'contact_type': 'primary',
                 'partner_id': OdooObject(odoo_cache['partners'][1]),
                 'cloud_tenant': 1, 'id': 16, },
            }

        tenant_partners = [OdooObject(partner[1]) for partner
                           in odoo_cache['project_rels'].items()]
        odoo_cache['projects'][1]['cloud_tenant_partners'] = tenant_partners

    def test_get_account_details(self):
        """
        Test getting account data.
        """
        url = "/v1/billing/account_details/"
        headers = {
            'project_name': self.project.name,
            'project_id': self.project.id,
            'roles': "project_admin,_member_,project_mod",
            'username': "test@example.com",
            'user_id': "test_user_id",
            'authenticated': True
        }

        response = self.client.get(url, headers=headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        resp_data = response.json()
        self.assertEqual(resp_data['customer_name'], 'The Company')
        self.assertEqual(resp_data['account_type'], 'organisation')
        self.assertEqual(
            resp_data['address'],
            {
                'address_1': 'a road',
                'address_2': '',
                'postal_code': '90210',
                'city': 'Wellington',
                'country': 'NZ',
                'country_name': 'New Zealand',
            })

    def test_update_account_details(self):
        """
        Test updating account data.
        """
        url = "/v1/billing/account_details/"
        headers = {
            'project_name': self.project.name,
            'project_id': self.project.id,
            'roles': "project_admin,_member_,project_mod",
            'username': "test@example.com",
            'user_id': "test_user_id",
            'authenticated': True
        }

        data = {
            'name': 'The Company',
            'address_1': 'another road',
            'address_2': '',
            'postal_code': 'NW1',
            'city': 'Wellington',
            'country': 'NZ',
        }

        response = self.client.post(url, data, headers=headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        odooclient = get_odoo_client()

        search = [
            ('is_company', '=', True),
            ('name', '=', 'The Company')
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].country_id.code, 'NZ')
        self.assertEquals(partners[0].property_account_position, False)
        self.assertEquals(partners[0].street, 'another road')
        self.assertEquals(partners[0].zip, 'NW1')
        self.assertIn(
            "Partner address has changed. Prior address was:",
            partners[0].message_ids[0].body)

    def test_update_account_details_country(self):
        """
        Test updating account data country, which will need approval.
        """
        url = "/v1/billing/account_details/"
        headers = {
            'project_name': self.project.name,
            'project_id': self.project.id,
            'roles': "project_admin,_member_,project_mod",
            'username': "test@example.com",
            'user_id': "test_user_id",
            'authenticated': True
        }

        data = {
            'name': 'The Company',
            'address_1': 'another road',
            'address_2': '',
            'postal_code': 'NW1',
            'city': 'Wellington',
            'country': 'GB',
        }

        response = self.client.post(url, data, headers=headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        odooclient = get_odoo_client()

        # confirm details haven't changed yet
        search = [
            ('is_company', '=', True),
            ('name', '=', 'The Company')
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].country_id.code, 'NZ')
        self.assertEquals(partners[0].property_account_position, False)
        self.assertEquals(partners[0].street, 'a road')
        self.assertEquals(partners[0].zip, '90210')

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

        search = [
            ('is_company', '=', True),
            ('name', '=', 'The Company')
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].country_id.code, 'GB')
        self.assertEquals(partners[0].property_account_position, 1)
        self.assertEquals(partners[0].street, 'another road')
        self.assertEquals(partners[0].zip, 'NW1')

        self.assertIn(
            "Partner address has changed. Prior address was:",
            partners[0].message_ids[0].body)

    def test_update_account_details_name(self):
        """
        Test updating customer name.
        """
        url = "/v1/billing/account_details/"
        headers = {
            'project_name': self.project.name,
            'project_id': self.project.id,
            'roles': "project_admin,_member_,project_mod",
            'username': "test@example.com",
            'user_id': "test_user_id",
            'authenticated': True
        }

        data = {
            'name': 'The Other Company',
            'address_1': 'another road',
            'address_2': '',
            'postal_code': '90210',
            'city': 'Wellington',
            'country': 'NZ',
        }

        response = self.client.post(url, data, headers=headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        odooclient = get_odoo_client()

        # NOTE(adriant): search confirms the name change worked.
        search = [
            ('is_company', '=', True),
            ('name', '=', 'The Other Company')
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].country_id.code, 'NZ')
        self.assertEquals(partners[0].street, 'another road')

        self.assertIn(
            "Partner has changed their name from:",
            partners[0].message_ids[0].body)
        self.assertIn(
            "Partner address has changed. Prior address was:",
            partners[0].message_ids[0].body)

    def test_no_resellers_allowed(self):
        """
        Test that a project with the reseller customer relationship gets a 403
        when the decorator is used (all views have the decorator).
        """
        odooclient = get_odoo_client()
        odoo_project = odooclient.projects.get(1)[0]
        odoo_partner = odooclient.partners.get(3)[0]

        odooclient.project_relationships.create(
            cloud_tenant=odoo_project.id,
            partner_id=odoo_partner.id,
            contact_type="reseller customer")

        url = "/v1/billing/account_details/"
        headers = {
            'project_name': self.project.name,
            'project_id': self.project.id,
            'roles': "project_admin,_member_,project_mod",
            'username': "test@example.com",
            'user_id': "test_user_id",
            'authenticated': True
        }

        data = {
            'po_number': 'Sale02',
        }

        response = self.client.post(url, data, headers=headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['is_reseller_customer'], True)
