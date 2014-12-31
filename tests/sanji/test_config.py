# __test__ = False
from __future__ import print_function

import os
import sys
import json

if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest2 as unittest

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.config import VersionDict
    from sanji.config import SanjiConfig
except ImportError:
    print("Please check the python PATH for import test module. (%s)"
          % __file__)
    exit(1)

import os
import shutil


class TestVersionDictClass(unittest.TestCase):
    """
    " Test class
    """

    def setUp(self):
        """
        " Prepare
        """
        self.vd = VersionDict()

    def tearDown(self):
        """
        " Clean up
        """
        self.vd = None

    def test_init(self):
        """
        " Test __init__()
        """
        self.vd = VersionDict()
        self.assertEqual(self.vd, {})
        test_dict = {"version": 0}
        self.assertEqual(test_dict, self.vd.get_private())
        self.assertEqual({}, self.vd.store[self.vd.public_head])
        self.assertEqual(test_dict, self.vd.store[self.vd.private_head])

    def test_getitem(self):
        """
        " test __getitem__()
        """
        private = self.vd.store[self.vd.private_head]
        self.vd["name"] = "John"
        self.vd["tree"] = {}
        self.vd["tree"]["node"] = 55688
        self.assertEqual("John", self.vd["name"])
        self.assertEqual(55688, self.vd["tree"]["node"])
        self.assertEqual(private, self.vd.store[self.vd.private_head])

    def test_setitem(self):
        """
        " test __setitem__()
        """
        private = self.vd.store[self.vd.private_head]
        self.vd["name"] = "John"
        self.vd["tree"] = {}
        self.vd["tree"]["node"] = 55688
        self.assertEqual("John", self.vd["name"])
        self.assertEqual(55688, self.vd["tree"]["node"])
        self.assertEqual(private, self.vd.store[self.vd.private_head])

    def test_delitem(self):
        private = self.vd.store[self.vd.private_head]
        self.vd["name"] = "John"
        self.vd["tree"] = {}
        self.vd["tree"]["node"] = 55688

        del self.vd["name"]
        with self.assertRaises(KeyError):
            self.vd["name"]

        del self.vd["tree"]
        with self.assertRaises(KeyError):
            self.vd["node"]
        with self.assertRaises(KeyError):
            self.vd["tree"]
        self.assertEqual(private, self.vd.store[self.vd.private_head])

    def test_iter(self):
        self.vd["tree"] = []
        self.vd["tree"].append(1)
        self.vd["tree"].append(1)
        self.vd["tree"].append(2)
        self.vd["tree"].append(3)
        self.vd["tree"].append(5)
        self.vd["tree"].append(8)
        self.vd["tree"].append(13)
        self.vd["tree"].append(21)
        self.vd["tree"].append(34)
        result_list = [0, 0, 1, 2, 4, 7, 12, 20, 33]
        for i in self.vd["tree"]:
            self.assertEqual(i - 1, result_list.pop(0))

    def test_len(self):
        pattern = [1, 3, 2, 4, 5, "color", {}]
        self.vd["name"] = "Lenny"
        self.vd["list"] = []
        for i in pattern:
            self.vd["list"].append(i)

        self.vd.store[self.vd.private_head]["hidden"] = "Monster"
        self.assertEqual(len(self.vd), 2)

    def test_str(self):
        self.vd["name"] = "Lenny"
        self.assertEqual(self.vd.__str__(), "{'name': 'Lenny'}")

    def test_repr(self):
        self.vd["name"] = "Lenny"
        self.assertEqual(self.vd.__repr__(), {'name': 'Lenny'})

    def test_construct_node(self):
        self.vd.construct_node("protected")
        self.assertEqual(self.vd, {})
        self.assertEqual(self.vd.store["protected"], {})
        self.vd.store["protected"] = 404
        self.assertEqual(self.vd.store["protected"], 404)

    def test_add_private_node(self):
        self.assertEqual(self.vd.add_private_node(), {"version": 0})

    def test_get_private(self):
        self.assertEqual(self.vd.store[self.vd.private_head],
                         self.vd.get_private())


class TestSanjiConfigClass(unittest.TestCase):
    """
    " Test class
    """
    json_name = "model.json"
    model_path = "/tmp/sanji-sdk/tests/test_config"
    model_db_folder = "/tmp/sanji-sdk/tests/test_config/data"
    model_json = "/tmp/sanji-sdk/tests/test_config/data/model.json"

    def setUp(self):
        """
        " Prepare
        """
        if os.path.exists(self.model_path):
            shutil.rmtree(self.model_path)

        os.makedirs(self.model_db_folder)

        json_config = {
            "public": {
                "A": 1234
            },
            "private": {
                "version": 0
            }
        }

        with open(self.model_json, "w") as db_file:
            json.dump(json_config, db_file, indent=4)

        self.sc = SanjiConfig(self.model_json)

    def tearDown(self):
        """
        " Clean up
        """
        if os.path.exists(self.model_path):
            shutil.rmtree(self.model_path)
        self.sc = None

    def test_init(self):
        """
        " Test __init__()
        """
        self.assertEqual(self.sc, {"A": 1234})

    def test_load(self):
        """
        "
        """
        json_config = {
            "public": {
                "A": 5566,
                "name": "Taiwan First Group"
            },
            "private": {
                "version": 2014
            }
        }
        with open(self.model_json, "w") as db_file:
            json.dump(json_config, db_file, indent=4)

        self.sc.load(self.model_json)
        self.assertEqual(self.sc.store["public"]["A"], 5566)
        self.assertEqual(self.sc.store["public"]["name"], "Taiwan First Group")
        self.assertEqual(self.sc.store["private"]["version"], 2014)

        self.sc.store = {}
        self.sc.load()
        self.assertEqual(self.sc.store["public"]["A"], 5566)

        empty_json = {}
        with open(self.model_json, "w") as db_file:
            json.dump(empty_json, db_file, indent=4)

        self.sc.load(self.model_json)
        self.assertEqual(self.sc.store["public"], {})
        self.assertEqual(self.sc.store["private"], {"version": 0})

    def test_save(self):
        """
        "
        """
        self.sc["fib"] = []
        self.sc["fib"].append(1)
        self.sc["fib"].append(1)
        self.sc["fib"].append(2)
        self.sc["fib"].append(3)
        self.sc["fib"].append(5)
        self.sc.save()

        with open(self.model_json, "r") as db_file:
            new_json = json.load(db_file)

        self.assertEqual(new_json, self.sc.store)


if __name__ == "__main__":
    unittest.main()
