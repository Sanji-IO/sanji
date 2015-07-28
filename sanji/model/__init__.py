from sanji.model_initiator import ModelInitiator
from voluptuous import Schema


class Model(object):
    def __init__(self, name, path, schema=None):
        if schema is not None:
            if not isinstance(schema, Schema):
                raise TypeError(
                    "schema should be instance of voluptuous.Schema")
            self.schema = schema
        else:
            self.schema = None

        self.model = ModelInitiator(
            model_name=name,
            model_path=path
        )

    @property
    def maxId(self):
        """int: current max id of objects"""
        if len(self.model.db) == 0:
            return 0

        return max(map(lambda obj: obj["id"], self.model.db))

    def validation(self, instance):
        """Valid input instance is vaild or not
            Args:
                Object: input instance
            Returns:
                Object: Instance after vaildation or original instance
                        if schema is None
            Raises:
                Error: If vaildation failed
        """
        if self.schema is None:
            return instance

        return self.schema(instance)

    def add(self, obj):
        """Add a object
            Args:
                Object: Object will be added
            Returns:
                Object: Object with id
            Raises:
                TypeError: If add object is not a dict
                MultipleInvalid: If input object is invaild
        """
        if isinstance(obj, list):
            raise TypeError("Add object should be a dict object")

        obj = self.validation(obj)
        obj["id"] = self.maxId + 1
        self.model.db.append(obj)

        return obj

    def get(self, id):
        """Get a object by id
            Args:
                id (int): Object id

            Returns:
                Object: Object with specified id
                None: If object not found
        """
        for obj in self.model.db:
            if obj["id"] == id:
                return obj

        return None

    def remove(self, id):
        """Remove a object by id
            Args:
                id (int): Object's id should be deleted
            Returns:
                None
        """
        self.model.db = [t for t in self.model.db if t["id"] != id]

    def update(self, id, newObj):
        """Update a object
            Args:
                id (int): Object's id will be updated
                newObj (object): New object will be merged into original object
            Returns:
                Object: Updated object
                None: If specified object id is not found
                MultipleInvalid: If input object is invaild
        """
        newObj = self.validation(newObj)
        for obj in self.model.db:
            if obj["id"] != id:
                continue
            newObj.pop("id", None)
            obj.update(newObj)
            return obj

        return None

    def getAll(self):
        """Get all objects
            Returns:
                List: list of all objects
        """
        return self.model.db
