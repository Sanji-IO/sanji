from sanji.model_initiator import ModelInitiator
from voluptuous import Schema


class Model(object):

    def __init__(self, name, path, schema=None, model_cls=dict):
        self.model_cls = model_cls
        self.schema = schema
        if schema is not None and not isinstance(schema, Schema):
            raise TypeError("schema should be instance of voluptuous.Schema")

        if not issubclass(model_cls, dict):
            raise TypeError("model_cls should be derivative dict class")

        self.model = ModelInitiator(
            model_name=name,
            model_path=path
        )

    def _cast_model(self, obj):
        return self.model_cls(obj)

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
        if not isinstance(obj, dict):
            raise TypeError("Add object should be a dict object")
        obj = self.validation(obj)
        obj = self._cast_model(obj)
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
                return self._cast_model(obj)

        return None

    def remove(self, id):
        """Remove a object by id
            Args:
                id (int): Object's id should be deleted
            Returns:
                len(int): affected rows
        """
        before_len = len(self.model.db)
        self.model.db = [t for t in self.model.db if t["id"] != id]
        return before_len - len(self.model.db)

    def removeAll(self):
        """Remove all objects
            Returns:
                len(int): affected rows
        """
        before_len = len(self.model.db)
        self.model.db = []
        return before_len - len(self.model.db)

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
            obj = self._cast_model(obj)
            return obj

        return None

    def getAll(self):
        """Get all objects
            Returns:
                List: list of all objects
        """
        objs = []
        for obj in self.model.db:
            objs.append(self._cast_model(obj))

        return objs
