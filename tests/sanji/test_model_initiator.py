import json
import unittest
import shutil
import sys
import os

from mock import patch

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.model_initiator import ModelInitiator
except ImportError:
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
    exit(1)


class TestModelInitiatorClass(unittest.TestCase):
    """
    " Test class
    """

    model_name = "test_myself"
    model_path = "/tmp/sanji-sdk/tests/test_myself"
    model_db_folder = "/tmp/sanji-sdk/tests/test_myself/data"
    model_factory_db = \
        "/tmp/sanji-sdk/tests/test_myself/data/test_myself.factory.json"
    model_db = "/tmp/sanji-sdk/tests/test_myself/data/test_myself.json"

    def setUp(self):
        """
        " Prepare
        """
        factory_data = {}
        factory_data["name"] = "factory"
        os.makedirs(self.model_db_folder)
        with open(self.model_factory_db, "w") as fp:
            json.dump(factory_data, fp, indent=4)
        self.model_initaitor = ModelInitiator(self.model_name, self.model_path)

    def tearDown(self):
        """
        " Clean up
        """
        if os.path.exists(self.model_path):
            shutil.rmtree(self.model_path)

        self.model_initaitor = None

    def test_init(self):
        """
        " Test __init__()
        """
        self.assertEquals(self.model_initaitor.model_name, self.model_name)

    def test_create_db(self):
        """
        " It should generate a factory db if there is no db.
        """
        if os.path.exists(self.model_db_folder):
            shutil.rmtree(self.model_db_folder)
        os.makedirs(self.model_db_folder)
        try:
            with open(self.model_factory_db, "a"):
                os.utime(self.model_factory_db, None)
        except Exception:
            self.fail("Maybe there is no folder to create file.")

        result = self.model_initaitor.create_db()
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.model_db))

        self.db_type = "sql"
        result = self.model_initaitor.create_db()
        self.assertFalse(result)

    def test_load_db(self):
        """
        " It should load json db as a dictionary.
        """
        self.model_initaitor.db = None
        self.assertEqual(type(self.model_initaitor.db), type(None))
        self.model_initaitor.create_db()
        try:
            with open(self.model_factory_db, "a"):
                os.utime(self.model_factory_db, None)
        except Exception:
            self.fail("Maybe there is no folder to create file.")

        data = {}
        data["enable"] = 1
        with open(self.model_factory_db, "w") as fp:
            json.dump(data, fp, indent=4)

        shutil.copyfile(self.model_factory_db, self.model_db)
        self.model_initaitor.load_db()
        self.assertEqual(self.model_initaitor.db, data)

    def test_save_db(self):
        self.model_initaitor.db = {}
        self.model_initaitor.db["name"] = "John"
        self.model_initaitor.db["age"] = 33
        self.model_initaitor.save_db()
        db_data = None
        with open(self.model_db) as fp:
            db_data = json.load(fp)

        self.assertEqual(db_data, {"name": "John", "age": 33})


if __name__ == "__main__":
    unittest.main()
