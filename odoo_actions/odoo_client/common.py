
class BaseManager(object):

    # you must initialise self.resource_env in __init__

    class Meta:
        abstract = True

    def _list_or_tuple(self, ids):
        if not isinstance(ids, list) or isinstance(ids, tuple):
            ids = [ids, ]
        return ids

    def get(self, ids):
        """Get one or more Resources by id.

        'ids' can be 1 id, or a list of ids.

        <resource>.get(<id>) returns: [<object_of_id>]
        <resource>.get([<id>]) returns: [<object_of_id>]
        <resource>.get([<id_1>, <id_2>]) returns:
            [<object_of_id_1>, <object_of_id_2>]

        Always returns a list even when 1 id is given.
        This is done for consistency.
        """
        return self.resource_env.browse(self._list_or_tuple(ids))

    def list(self, filters):
        """Get a list of Resources.

        'filters' is a list of search options.`
            [('field', '=', value), ]
        """
        ids = self.resource_env.search(filters)
        return self.get(ids)

    def create(self, **fields):
        """Create a Resource.

        'fields' is the dict of kwargs to pass to create.
        Allows slighly nicer syntax than having to pass in a dict.
        """
        return self.resource_env.create(fields)

    def load(self, fields, rows):
        """Loads in a Resource.

        'fields' is a list of fields to import. - list(str)
        'rows' is the item data. - list(list(str))
        """
        return self.resource_env.create(fields)

    def delete(self, ids):
        """Delete 1 or more Resources by id.

        'ids' can be 1 id, or a list of ids.

        <resource>.delete(<id>) deletes: <object_of_id>
        <resource>.delete([<id>]) deletes: <object_of_id>
        <resource>.delete([<id_1>, <id_2>]) deletes:
            <object_of_id_1> and <object_of_id_2>

        returns True if deleted or not present.
        """
        return self.resource_env.unlink(self._list_or_tuple(ids))
