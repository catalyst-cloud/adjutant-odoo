import six


odoo_cache = {}
base_id = 1


def _get_new_id():
    global base_id
    return_id = base_id
    base_id += 1
    return return_id


class OdooObject(object):
    def __init__(self, fields):
        self.__dict__.update(fields)


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
            resources.append(
                OdooObject(self.odoo_cache[self.resource].get(res_id)))
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


class FakeOdooClient(object):

    def __init__(self):
        # Now setup the managers:
        self.projects = FakeOdooResourceManager("projects")
        self.partners = FakePartnerManager("partners")
        self.project_relationships = FakeOdooResourceManager("project_rels")


def setup_odoo_cache():
    global odoo_cache
    odoo_cache.clear()
    odoo_cache.update({
        'projects': {},
        'partners': {},
        'project_rels': {},
    })


def get_odoo_client():
    return FakeOdooClient()
