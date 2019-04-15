from collections import Iterable


class BaseManager(object):

    # you must initialise self.resource_env in __init__

    fields = None

    class Meta:
        abstract = True

    def _is_iterable(self, ids):
        if isinstance(ids, str) or not isinstance(ids, Iterable):
            ids = [ids, ]
        return ids

    def get(self, ids, read=False):
        """Get one or more Resources by id.

        'ids' can be 1 id, or a list of ids.

        <resource>.get(<id>) returns: [<object_of_id>]
        <resource>.get([<id>]) returns: [<object_of_id>]
        <resource>.get([<id_1>, <id_2>]) returns:
            [<object_of_id_1>, <object_of_id_2>]

        Always returns a list even when 1 id is given.
        This is done for consistency.
        """
        if read:
            return self.resource_env.read(
                self._is_iterable(ids), fields=self.fields)
        return self.resource_env.browse(self._is_iterable(ids))

    def list(self, filters, get=True, read=False):
        """Get a list of Resources.

        'filters' is a list of search options.`
            [('field', '=', value), ]
        """
        ids = self.resource_env.search(filters)
        if get:
            return self.get(ids, read)
        else:
            return ids

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
        return self.resource_env.load(fields=fields, data=rows)

    def delete(self, ids):
        """Delete 1 or more Resources by id.

        'ids' can be 1 id, or a list of ids.

        <resource>.delete(<id>) deletes: <object_of_id>
        <resource>.delete([<id>]) deletes: <object_of_id>
        <resource>.delete([<id_1>, <id_2>]) deletes:
            <object_of_id_1> and <object_of_id_2>

        returns True if deleted or not present.
        """
        return self.resource_env.unlink(self._is_iterable(ids))
