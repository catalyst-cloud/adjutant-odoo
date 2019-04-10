import six
from mock import MagicMock
from collections import Iterable

odoo_cache = {}
base_id = 20  # NOTE(amelia): Set at twenty to avoid conflicts with any setup


INDIVIDUAL_TAG_ID = 7


def _get_new_id():
    global base_id
    return_id = base_id
    base_id += 1
    return return_id


class OdooObject(object):
    def __init__(self, fields):
        self.fields = fields
        if 'country_id' in fields:
            country_id = fields.pop('country_id')
            if type(country_id) == OdooObject:
                self.country_id = country_id
            elif country_id is False:
                self.country_id = OdooObject({})
            elif type(country_id) == dict:
                self.country_id = OdooObject(country_id)
            else:
                self.country_id = OdooObject(
                    odoo_cache['countries'][country_id])

        if 'category_id' in fields:
            category_id = fields.pop('category_id')
            if (category_id and type(category_id) == list and
                    type(category_id[0]) == tuple):
                self.category_id = [
                    OdooObject(odoo_cache['tags'][tag])
                    for tag in category_id[0][2]
                ]
            else:
                self.category_id = category_id
        self.__dict__.update(fields)

    def __setattr__(self, name, value):
        if name not in ['fields', 'default']:
            self.fields[name] = value
        if name == 'country_id' and type(value) == int:
            self.fields[name] = OdooObject(
                odoo_cache['countries'][value])

        super(OdooObject, self).__setattr__(name, value)

    def __getattr__(self, name):
        if name == 'env':
            return MagicMock()
        return None

    def __str__(self):
        fields_pairs = []
        for key, value in self.fields.items():
            fields_pairs.append("%s=%s" % (key, value))
        return "OdooObject(%s)" % ", ".join(fields_pairs)
    __repr__ = __str__

    def __getitem__(self, index):
        """Quick and dirty hack to support the OdooObject acting as
        an (id, name) tuple."""

        if index == 0:
            return self.id
        return None


class FakeOdooResourceManager(object):

    defaults = {}

    def __init__(self, resource):
        self.resource = resource

        global odoo_cache
        self.odoo_cache = odoo_cache

    def _is_iterable(self, ids):
        if isinstance(ids, str) or not isinstance(ids, Iterable):
            ids = [ids, ]
        return ids

    def get(self, ids, read=False):
        resources = []
        for res_id in self._is_iterable(ids):
            res = self.odoo_cache[self.resource].get(res_id)
            if res:
                if read:
                    resources.append(res)
                else:
                    resources.append(OdooObject(res))
        return resources

    def list(self, filters, read=False):
        """
        For the purposes of this mocking... we will assume that the '|'
        operator is not used, just the implicit AND.
        """
        resources = []
        for resource in six.itervalues(self.odoo_cache[self.resource]):
            match = True
            for key, operator, value in filters:
                res_val = resource.get(key)
                if isinstance(res_val, OdooObject):
                    res_val = res_val.id

                if operator == "=":
                    if res_val != value:
                        match = False
                        break
                elif operator == "!=":
                    if res_val == value:
                        match = False
                        break
                elif operator == "in":
                    if res_val not in value:
                        match = False
                        break
            if match:
                if read:
                    resources.append(resource)
                else:
                    resources.append(OdooObject(resource))
        return resources

    def create(self, **fields):
        res_id = _get_new_id()
        fields['id'] = res_id

        # handle defaults
        for key, value in self.defaults.items():
            if key not in fields:
                fields[key] = value

        self.odoo_cache[self.resource][res_id] = fields
        return res_id

    def delete(self, res_ids):
        res_ids = self._is_iterable(res_ids)
        for res_id in res_ids:
            del self.odoo_cache[self.resource][res_id]


class FakePartnerManager(FakeOdooResourceManager):

    defaults = {
        'is_company': False,
        'street2': False,
        'category_id': [],
    }

    def fuzzy_match(self, name, is_company=False, check_parent=False,
                    parent=None):

        search = [
            ('is_company', '=', is_company),
            ('name', '=', name)
        ]

        if check_parent:
            search.append(('parent_id', '=', parent))

        # Should be a server side call to:
        # self.resource_env.fuzzy_match(<args>)
        customers = self.list(search)

        matches = []
        for customer in customers:
            matches.append({
                'id': customer.id,
                'name': customer.name,
                # Odoo will give us this value eventually, for now
                # we hardcode it to 1 because these are exact matches.
                'match': 1
            })

        return matches

    def add_internal_note(self, partner_id, body, **kwargs):
        partner = self.odoo_cache[self.resource][partner_id]
        message = {'body': body}
        message.update(kwargs)
        message = OdooObject(message)
        if not partner.get('message_ids'):
            partner['message_ids'] = []
        partner['message_ids'].append(message)


class FakeCountryManager(FakeOdooResourceManager):

    def fuzzy_match(self, code):
        search = [
            ('code', '=', code)
        ]

        return self.list(search)

    def get_closest_country(self, code):
        return self.fuzzy_match(code)[0]


class FakeRelationshipManager(FakeOdooResourceManager):

    def get_editable_contact_types(self):
        return ['billing', 'technical', 'legal']


class FakeOdooClient(object):

    def __init__(self):
        # Now setup the managers:
        self.projects = FakeOdooResourceManager("projects")
        self.partners = FakePartnerManager("partners")
        self.project_relationships = FakeOdooResourceManager("project_rels")
        self.project_relationships = FakeRelationshipManager("project_rels")
        self.countries = FakeCountryManager("countries")
        self.credits = FakeCountryManager("credits")
        self.tags = FakeOdooResourceManager("tags")
        self.stripe_partners = FakeOdooResourceManager("stripe_partners")
        self._odoorpc = MagicMock()


def setup_odoo_cache():
    global odoo_cache
    odoo_cache.clear()
    odoo_cache.update({
        'projects': {},
        'partners': {},
        'project_rels': {},
        'countries': {
            1: {'name': 'United Kingdom', 'code': 'GB', 'id': 1},
            2: {'name': 'Saint Helena', 'code': 'SH', 'id': 2},
            3: {'name': 'New Zealand', 'code': 'NZ', 'id': 3},
            4: {'name': 'Australia', 'code': 'AU', 'id': 4}
        },
        'credits': {},
        'tags': {
            1: {'name': 'cloud tag', 'id': 1},
            INDIVIDUAL_TAG_ID: {
                'name': 'cloud tag', 'id': INDIVIDUAL_TAG_ID},
        },
        'stripe_partners': {}
    })

    global base_id
    base_id = 20


def get_odoo_client():
    return FakeOdooClient()
