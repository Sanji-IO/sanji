from __future__ import print_function

import os
import sys
import tempfile
import simplejson as json
from voluptuous import Schema
from voluptuous import MultipleInvalid

if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest2 as unittest

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../../')
    from sanji.model import Model
except ImportError:
    print("Please check the python PATH for import test module.")
    exit(1)


class TestModelClass(unittest.TestCase):

    def setUp(self):
        factory_data = []
        self.temp_dir = tempfile.mkdtemp("test_model")
        os.mkdir(self.temp_dir + "/data")
        with open(self.temp_dir + "/data/test.json.factory", "w") as fp:
            json.dump(factory_data, fp)
        with open(self.temp_dir + "/data/schema.json.factory", "w") as fp:
            json.dump(factory_data, fp)
        self.model = Model(name="test", path=self.temp_dir)
        self.model.add({"key": "value1"})
        self.model.add({"key": "value2"})
        self.model.add({"key": "value3"})

        schema = Schema({"key": int})
        self.model_with_schema = Model(
            name="schema", path=self.temp_dir, schema=schema)

    def test__init__(self):
        """Create a Model instance with wrong schema type,
            should raise TypeError"""
        with self.assertRaises(TypeError):
            Model(name="test", path="/tmp", schema={"key": int})

    def test__init__invaild_model_cls(self):
        """Create a Model instance with wrong model_cls type,
            should raise TypeError"""
        with self.assertRaises(TypeError):
            Model(name="test", path="/tmp", model_cls=list)

    def test_add(self):
        """Add an object, should return inserted object with id"""
        newObj = self.model.add({"key": "value"})
        self.assertEqual(newObj["id"], 4)

    def test_add_invaild(self):
        """Add an invaild object, should raise RuntimeError"""
        with self.assertRaises(TypeError):
            self.model.add(["test"])

    def test_add_invaild_schema(self):
        """Add an invaild object(against schema),
            should raise MutlitpleInvalid"""
        with self.assertRaises(MultipleInvalid):
            self.model_with_schema.add({"key": []})

    def test_get(self):
        """Get an object by id, should return correct object"""
        obj = self.model.get(3)
        self.assertEqual(obj["key"], "value3")

    def test_getAll(self):
        """Get all objects, should return all of objects"""
        objs = self.model.getAll()
        self.assertTrue(isinstance(objs, list))
        self.assertEqual(len(objs), 3)

    def test_remove(self):
        """Delete an object with specified id, should return nothing"""
        self.model.remove(1)
        self.assertEqual(self.model.get(1), None)

    def test_removeAll(self):
        """Delete all objects, should return nothing"""
        self.model.removeAll()
        objs = self.model.getAll()
        self.assertEqual(len(objs), 0)

    def test_update(self):
        """Update object, should return new object"""
        new_obj = self.model.update(1, {"key": "updated value"})
        self.assertIsNotNone(new_obj)
        self.assertEqual(self.model.get(1)["key"], "updated value")

    def test_update_invaild(self):
        """Update an invaild object(against schema),
            should raise MutlitpleInvalid"""
        with self.assertRaises(MultipleInvalid):
            self.model_with_schema.update(1, {"key": "updated value"})

    def test_update_non_exist(self):
        """Update object which is not exist, should return None"""
        new_obj = self.model.update(10, {"key": "updated value"})
        self.assertIsNone(new_obj)

    def test_set(self):
        """Update object, should return new object"""
        new_obj = self.model.set(1, {
            "newkey": "updated value"
        })
        self.assertIsNotNone(new_obj)
        self.assertEqual(self.model.get(1)["newkey"], "updated value")
        self.assertNotIn("key", self.model.get(1))

    def test_set_invaild(self):
        """Update an invaild object(against schema),
            should raise MutlitpleInvalid"""
        with self.assertRaises(MultipleInvalid):
            self.model_with_schema.set(1, {"key": "updated value"})

    def test_set_non_exist(self):
        """Update object which is not exist, should return None"""
        new_obj = self.model.set(10, {"key": "updated value"})
        self.assertIsNone(new_obj)

    def test_batch_mode(self):
        """Test batch mode"""
        with self.model.batch():
            self.model.set(1, {"test": "I should not be saved."})
            with open(self.temp_dir + "/data/test.json", "r") as f:
                db = json.load(f)
                self.assertNotEqual(
                    self.model.get(1)["test"], db[0].get("test", None))

        with open(self.temp_dir + "/data/test.json", "r") as f:
            db = json.load(f)
            self.assertEqual(self.model.get(1)["test"], db[0].get("test"))

    def test_batch_mode_raise_error(self):
        """In batch mode, even raise error after set it will be saved"""
        try:
            with self.model.batch():
                self.model.set(1, {"test": "I should not be saved."})
                with open(self.temp_dir + "/data/test.json", "r") as f:
                    db = json.load(f)
                    self.assertNotEqual(
                        self.model.get(1)["test"], db[0].get("test", None))
                raise RuntimeError()
        except Exception:
            pass

        with open(self.temp_dir + "/data/test.json", "r") as f:
            db = json.load(f)
            self.assertEqual(self.model.get(1)["test"], db[0].get("test"))

    def test_batch_mode_error(self):
        """Test batch mode in batch mode, should raise RuntimeError"""
        with self.assertRaises(RuntimeError):
            with self.model.batch():
                with self.model.batch():
                    pass

if __name__ == "__main__":
    unittest.main()
