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

from decorator import decorator

from rest_framework.response import Response

from odoo_actions import odoo_client


# TODO(adriant): Once the project model has a dedicated reseller field, test
#                that instead.

@decorator
def not_reseller_customer(func, *args, **kwargs):
    """
    Ensure project isn't a resold customer
    """
    request = args[1]
    project_id = request.keystone_user['project_id']

    odooclient = odoo_client.get_odoo_client()

    try:
        odoo_project = odooclient.projects.list([
            ('tenant_id', '=', project_id)], read=True)[0]
    except IndexError:
        return Response({'errors': ['Project not found']}, status=404)

    reseller_customer_rels = odooclient.project_relationships.list([
        ('cloud_tenant', '=', odoo_project['id']),
        ('contact_type', '=', 'reseller customer')], read=True)

    if reseller_customer_rels:
        return Response(
            {'errors': ['Reseller customers cannot access this API.'],
             'is_reseller_customer': True},
            403)

    return func(*args, **kwargs)
