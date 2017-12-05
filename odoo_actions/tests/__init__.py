import six
from mock import MagicMock

odoo_cache = {}
base_id = 1


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
        if name not in ['fields', 'default', 'country_id']:
            self.fields[name] = value
        if name == 'country_id' and type(value) == OdooObject:
            self.fields[name] = value.id
        if name == 'country_id' and type(value) != OdooObject:
            self.fields[name] = value
        super(OdooObject, self).__setattr__(name, value)

    def __getattr__(self, name):
        if name == 'env':
            return MagicMock()
        return None


class FakeOdooResourceManager(object):

    def __init__(self, resource):
        self.resource = resource

        global odoo_cache
        self.odoo_cache = odoo_cache

    def _list_or_tuple(self, ids):
        if not isinstance(ids, list) or isinstance(ids, tuple):
            ids = [ids, ]
        return ids

    def get(self, ids):
        resources = []
        for res_id in self._list_or_tuple(ids):
            res = self.odoo_cache[self.resource].get(res_id)
            if res:
                resources.append(OdooObject(res))
        return resources

    def list(self, filters):
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
                resources.append(OdooObject(resource))
        return resources

    def create(self, **fields):
        res_id = _get_new_id()
        fields['id'] = res_id
        self.odoo_cache[self.resource][res_id] = fields
        return res_id

    def delete(self, res_ids):
        res_ids = self._list_or_tuple(res_ids)
        for res_id in res_ids:
            del self.odoo_cache[self.resource][res_id]


class FakePartnerManager(FakeOdooResourceManager):

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


class FakeCountryManager(FakeOdooResourceManager):

    def fuzzy_match(self, code):
        search = [
            ('code', '=', code)
        ]

        return self.list(search)

    def get_closest_country(self, code):
        return self.fuzzy_match(code)[0]


class FakeOdooClient(object):

    def __init__(self):
        # Now setup the managers:
        self.projects = FakeOdooResourceManager("projects")
        self.partners = FakePartnerManager("partners")
        self.project_relationships = FakeOdooResourceManager("project_rels")
        self.countries = FakeCountryManager("countries")
        self.tags = FakeOdooResourceManager("tags")
        self._odoo = MagicMock()


def setup_odoo_cache():
    global odoo_cache
    odoo_cache.clear()
    odoo_cache.update({
        'projects': {},
        'partners': {},
        'project_rels': {},
        'countries': {
            1: {'code': 'RD', 'id': 1},
            2: {'code': 'SH', 'id': 2},
            3: {'code': 'NZ', 'id': 3},
            4: {'code': 'AU', 'id': 4}
        },
        'tags': {
            1: {'name': 'cloud tag', 'id': 1},
        }
    })


def get_odoo_client():
    return FakeOdooClient()
