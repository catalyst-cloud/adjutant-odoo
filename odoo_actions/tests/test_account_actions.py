# Copyright (C) 2018 Catalyst IT Ltd
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

from django.test import TestCase
from django.test.utils import override_settings

import mock

from adjutant.api.models import Task
from adjutant.common.tests import fake_clients

from odoo_actions.account import UpdateAccountDetailsAction
from odoo_actions.tests import (
    odoo_cache, get_odoo_client, setup_odoo_cache, OdooObject)


@mock.patch('odoo_actions.odoo_client.get_odoo_client', get_odoo_client)
@mock.patch(
    'adjutant.common.user_store.IdentityManager', fake_clients.FakeManager)
@override_settings(PLUGIN_SETTINGS={'adjutant-odoo': {
    'fiscal_position_id': 1,
    'cloud_tag_id': 1,
    'non_fiscal_position_countries': ['NZ'],
    'physical_address_contact_name': 'Physical Address'
    }})
class AccountActionTests(TestCase):

    def setUp(self):
        setup_odoo_cache()

        self.project = fake_clients.FakeProject(
            name='Company Cloud Project')
        fake_clients.setup_identity_cache(projects=[self.project])

        odoo_cache['projects'] = {
            1: {
                'name': 'Company Cloud Project',
                'tenant_id': self.project.id,
                'id': 1}}
        odoo_cache['partners'] = {
            2: {
                'name': 'Cloud Company',
                'email': 'acontact@olddomain.com',
                'phone': '01234567',
                'parent_id': False,
                'id': 2,
                'is_company': True,
                'street': "A Street",
                'street2': False,
                'zip': 1010,
                'city': "A city",
                'country_id': odoo_cache['countries'][1]
                },
            }

        odoo_cache['project_rels'] = {
            12: {'contact_type': 'owner', 'id': 12,
                 'partner_id': OdooObject(odoo_cache['partners'][2]),
                 'cloud_tenant': OdooObject(odoo_cache['projects'][1])},
            }

    def test_update_account_details_address(self):
        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={})

        data = {
            'project_id': self.project.id,
            'name': 'Cloud Company',
            'address_1': "123 Street Street",
            'address_2': '',
            'postal_code': 12342,
            'city': 'Blasphemy',
            'country': 'NZ',
        }

        action = UpdateAccountDetailsAction(data, task=task, order=1)

        action.pre_approve()
        self.assertEquals(action.valid, True)

        action.post_approve()
        self.assertEquals(action.valid, True)

        odooclient = get_odoo_client()
        search = [
            ('is_company', '=', True),
            ('name', '=', 'Cloud Company')
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].country_id.code, 'NZ')
        self.assertEquals(partners[0].property_account_position, False)
        self.assertEquals(partners[0].street, '123 Street Street')

        self.assertIn(
            "Partner address has changed. Prior address was:",
            partners[0].message_ids[0].body)

        action.submit({})
        self.assertEquals(action.valid, True)

    def test_update_account_details_address_country(self):
        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={})

        data = {
            'project_id': self.project.id,
            'name': 'Cloud Company',
            'address_1': "123 Street Street",
            'address_2': '',
            'postal_code': 12342,
            'city': 'Blasphemy',
            'country': 'SH',
        }

        action = UpdateAccountDetailsAction(data, task=task, order=1)

        action.pre_approve()
        self.assertEquals(action.valid, True)
        # This action should not allow auto approval:
        self.assertEquals(action.auto_approve, False)

        # Now we approve it anyway
        action.post_approve()
        self.assertEquals(action.valid, True)

        odooclient = get_odoo_client()
        search = [
            ('is_company', '=', True),
            ('name', '=', 'Cloud Company')
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].country_id.code, 'SH')
        self.assertEquals(partners[0].property_account_position, 1)
        self.assertEquals(partners[0].street, '123 Street Street')

        action.submit({})
        self.assertEquals(action.valid, True)

    def test_update_account_details_name(self):
        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={})

        data = {
            'project_id': self.project.id,
            'name': 'Not Cloud Company',
            'address_1': "123 Street Street",
            'address_2': '',
            'postal_code': 12342,
            'city': 'Blasphemy',
            'country': 'NZ',
        }

        action = UpdateAccountDetailsAction(data, task=task, order=1)

        action.pre_approve()
        self.assertEquals(action.valid, True)

        action.post_approve()
        self.assertEquals(action.valid, True)

        # By finding it by name, we know the name change worked, no need to
        # assert
        odooclient = get_odoo_client()
        search = [
            ('is_company', '=', True),
            ('name', '=', 'Not Cloud Company')
        ]
        partners = odooclient.partners.list(search)
        self.assertEquals(len(partners), 1)
        self.assertEquals(partners[0].country_id.code, 'NZ')
        self.assertEquals(partners[0].property_account_position, False)
        self.assertEquals(partners[0].street, '123 Street Street')

        self.assertIn(
            "Partner has changed their name from:",
            partners[0].message_ids[0].body)
        self.assertIn(
            "Partner address has changed. Prior address was:",
            partners[0].message_ids[0].body)

        action.submit({})
        self.assertEquals(action.valid, True)
