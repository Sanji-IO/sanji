import unittest
import sys
import subprocess
try:
    sys.path.append('../src')
    from model_initiator import ModelInitiator
except ImportError:
    print "Please check the python PATH for import test module."
    exit(1)

import os
import shutil

class TestModelInitiatorClass(unittest.TestCase):
    """
    " Test class
    """

    model_name = "test_myself"
    model_path = "/samba/sanji-sdk/tests/test_myself"
    model_db_folder = "/samba/sanji-sdk/tests/test_myself/data"
    model_factory_db = \
        "/samba/sanji-sdk/tests/test_myself/data/test_myself.factory.json"
    model_db = "/samba/sanji-sdk/tests/test_myself/data/test_myself.json"

    def setUp(self):
        """
        " Prepare
        """
        cmd = "mkdir -p %s" % self.model_path
        subprocess.call(cmd, shell=True)
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


    def test_mkdir(self):
        """
        " It Should generate a data folder.
        """
        result = self.model_initaitor.mkdir()
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.model_db_folder))


    def test_create_db(self):
        """
        " It should generate a factory db.
        """
        self.model_initaitor.mkdir()
        try:
            with open(self.model_factory_db, 'a'):
                os.utime(self.model_factory_db, None)
        except Exception:
            self.fail("Maybe there is no folder to create file.")

        self.assertRaises(self.model_initaitor.create_db)

        result = self.model_initaitor.create_db()
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.model_db))


if __name__ == "__main__":
    unittest.main()
