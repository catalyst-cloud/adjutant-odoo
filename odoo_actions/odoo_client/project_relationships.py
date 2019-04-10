# Copyright 2016 Catalyst IT Limited
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from datetime import timedelta

from django.utils import timezone

from .common import BaseManager


contact_types_cache = None
last_cache_update = None

blacklisted_contact_types = [
    "owner",
    "primary",
    "reseller customer",
]


class ProjectRelationshipManager(BaseManager):

    def __init__(self, odooclient, contact_types_whitelist=None):
        self.client = odooclient
        self.resource_env = self.client._PartnerRelationship

        if contact_types_whitelist:
            self.contact_types_whitelist = contact_types_whitelist
        else:
            self.contact_types_whitelist = []

    def _get_contact_types(self):
        global contact_types_cache
        global last_cache_update

        now = timezone.now()
        expiry_date = now - timedelta(hours=24)

        if (not contact_types_cache or
                not last_cache_update or last_cache_update < expiry_date):
            last_cache_update = now
            contact_types_cache = [
                tag[0] for tag in
                self.resource_env._columns['contact_type'].selection]

        return list(contact_types_cache)

    def get_editable_contact_types(self):
        contact_types = self._get_contact_types()

        for blacklisted_contact_type in blacklisted_contact_types:
            if blacklisted_contact_type in contact_types:
                contact_types.remove(blacklisted_contact_type)
        return contact_types
