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

# import odoorpc or somesuch
# from django.conf import settings


cached_client = None


class OdooClient(object):
    """This is a wrapper for the OdooRPC client.

    Rather than using OdooRPC directly, make functions here that
    do the work on your behalf, thus leaving the odoorpc messiness
    out of other areas.
    """

    def __init__(self, conf):
        # setup odoo rpc
        self.odoorpc = object()

    def do_an_odoo_thing(self):
        return {}

    def do_another_odoo_thing(self, partner, id):
        return {}


def get_odoo_client():
    global cached_client
    if not cached_client:
        # get odoo auth setting from settings
        # setup client

        # Will need to figure out where in the settings to
        # setup the odoo auth stuff...
        conf = {}

        cached_client = OdooClient(conf)

    return cached_client
