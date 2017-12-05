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

from .common import BaseManager


class CountryManager(BaseManager):

    def __init__(self, odooclient):
        self.client = odooclient
        self.resource_env = self.client._Country

    def fuzzy_match(self, code, threshold=0.8):
        """Will find near matches

        Returns: list(dict())
            [{'id': 1, 'name': "bob", "match": 0.8}, ]

        This needs to be properly implented Odoo side.
        """

        search = [
            ('code', '=ilike', code)
        ]

        # Should be a server side call to:
        # self.resource_env.fuzzy_match(<args>)
        countries = self.list(search)

        matches = []
        for country in countries:
            matches.append({
                'id': country.id,
                'name': country.name,
                # Odoo will give us this value eventually, for now
                # we hardcode it to 1 because these are exact matches.
                'match': 1
            })

        return matches

    def get_closest_country(self, code):
        matches = self.fuzzy_match(code)

        return self.get(matches[0]['id'])[0]
