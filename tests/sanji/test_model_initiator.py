import logging
import json
import shutil
import sys
import os

from mock import patch
from mock import Mock
from mock import MagicMock

if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest2 as unittest

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.model_initiator import ModelInitiator
except ImportError:
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
    exit(1)

logger = logging.getLogger()

ERROR_STR = """Error removing %(path)s, %(error)s """


def rmgeneric(path, __func__):
    try:
        __func__(path)
    except OSError, (errno, strerror):
        logger.debug(ERROR_STR % {'path': path, 'error': strerror})


def removeall(path):

    if not os.path.isdir(path):
        return

    files = os.listdir(path)

    for x in files:
        fullpath = os.path.join(path, x)
        if os.path.isfile(fullpath):
            f = os.remove
            rmgeneric(fullpath, f)
        elif os.path.isdir(fullpath):
            removeall(fullpath)
            f = os.rmdir
            rmgeneric(fullpath, f)


class TestModelInitiatorClass(unittest.TestCase):
    """
    " Test class
    """

    model_name = "test_myself"
    model_path = "/tmp/sanji-sdk/tests/test_myself"
    model_db_folder = "/tmp/sanji-sdk/tests/test_myself/data"
    model_factory_db = \
        "/tmp/sanji-sdk/tests/test_myself/data/test_myself.json.factory"
    model_backup_db = \
        "/tmp/sanji-sdk/tests/test_myself/data/test_myself.json.backup"
    model_db = "/tmp/sanji-sdk/tests/test_myself/data/test_myself.json"

    def setUp(self):
        """
        " Prepare
        """
        factory_data = {"name": "factory"}
        if not os.path.exists(self.model_db_folder):
            os.makedirs(self.model_db_folder)
        with open(self.model_factory_db, "w") as fp:
            json.dump(factory_data, fp, indent=4)

        self.model_initiator = ModelInitiator(
            self.model_name, self.model_path, backup_interval=-1)

    def tearDown(self):
        """
        " Clean up
        """
        self.model_initiator.stop_backup()
        self.model_initiator = None

        if os.path.exists(self.model_path):
            removeall(self.model_db_folder)

    def test_init(self):
        """
        " Test __init__()
        """
        # case 1: check name
        self.assertEquals(self.model_initiator.model_name, self.model_name)

        # case 2: thread
        self.model_initiator = None
        self.model_initiator = ModelInitiator(
            self.model_name, self.model_path, backup_interval=1)
        self.assertEquals(self.model_initiator.model_name, self.model_name)

    def test_db_manager(self):
        # case 1: existing
        self.model_initiator.save_db()
        self.model_initiator.db_manager()
        self.assertEqual(self.model_initiator.db_status, "existing")

        # case 2: factory
        with patch(
                "sanji.model_initiator.ModelInitiator.create_db")as create_db:
            create_db.return_value = 1
            if os.path.exists(self.model_db):
                os.remove(self.model_db)
            self.model_initiator = ModelInitiator(
                self.model_name, self.model_path, backup_interval=-1)

            self.assertTrue(os.path.exists(self.model_db))
            self.assertEqual(self.model_initiator.db_status, "factory")

        # case 3: backup
        with patch(
                "sanji.model_initiator.ModelInitiator.create_db")as create_db:
            create_db.return_value = 1
            self.model_initiator.save_db()
            self.model_initiator.backup_db()
            if os.path.exists(self.model_db):
                os.remove(self.model_db)
            self.model_initiator.db_manager()
            self.assertTrue(os.path.exists(self.model_db))
            self.assertEqual(self.model_initiator.db_status, "backup")

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

        # case 1: general case
        result = self.model_initiator.create_db()
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.model_db))

        # case 2: no factory db
        if os.path.exists(self.model_db):
            os.remove(self.model_db)
        if os.path.exists(self.model_factory_db):
            os.remove(self.model_factory_db)
        result = self.model_initiator.create_db()
        self.assertFalse(result)

        # case 3: sql type
        self.db_type = "sql"
        result = self.model_initiator.create_db()
        self.assertFalse(result)

    def test_recover_db(self):
        # case 1: Check file which restore from backup db
        self.model_initiator.db = {}
        self.model_initiator.db["name"] = "backup"
        self.model_initiator.db["type"] = "json"
        self.model_initiator.save_db()
        self.model_initiator.backup_db()
        if os.path.exists(self.model_db):
            os.remove(self.model_db)
        self.assertFalse(os.path.exists(self.model_db))
        self.model_initiator.recover_db(self.model_backup_db)
        self.assertTrue(os.path.exists(self.model_db))
        # case 2: Check data which restore from backup db
        with open(self.model_db) as fp:
            db_data = json.load(fp)

        self.assertEqual(db_data, {"name": "backup", "type": "json"})

        # case 3: Check file which restore from factory db
        if os.path.exists(self.model_db):
            os.remove(self.model_db)
        self.assertFalse(os.path.exists(self.model_db))
        self.model_initiator.recover_db(self.model_factory_db)
        self.assertTrue(os.path.exists(self.model_db))

        # case 4: Check data which restore from factory db
        with open(self.model_db) as fp:
            db_data = json.load(fp)

        self.assertEqual(db_data, {"name": "factory"})

        # case 5: no file
        try:
            self.assertRaises(
                self.model_initiator.recover_db("/tmp/1234555555.txt"))
        except IOError:
            pass
        else:
            self.fail("No file to load but pass.")

    def test_backup_db(self):
        """
        " Test backup db
        """
        if os.path.exists(self.model_backup_db):
            os.remove(self.model_backup_db)
        # case 1: Check file exist
        self.model_initiator.backup_db()
        self.assertTrue(os.path.exists(self.model_backup_db))

        # case 2: Check data
        with open(self.model_backup_db) as fp:
            db_data = json.load(fp)

        self.assertEqual(db_data, {"name": "factory"})

    def test_load_db(self):
        """
        " It should load json db as a dictionary.
        """
        # case 1: No folder
        self.model_initiator.db = None
        self.assertEqual(type(self.model_initiator.db), type(None))
        self.model_initiator.create_db()
        try:
            with open(self.model_factory_db, "a"):
                os.utime(self.model_factory_db, None)
        except Exception:
            self.fail("Maybe there is no folder to create file.")

        # case 2: data
        data = {"enable": 1}
        with open(self.model_factory_db, "w") as fp:
            json.dump(data, fp, indent=4)

        shutil.copyfile(self.model_factory_db, self.model_db)
        self.model_initiator.load_db()
        self.assertEqual(self.model_initiator.db, data)

        # case 3:
        if os.path.exists(self.model_db):
            os.remove(self.model_db)
            try:
                self.assertRaises(self.model_initiator.load_db())
            except Exception:
                pass

    def test_save_db(self):
        """
        " Test save db
        """
        # case 1: data of saving
        self.model_initiator.db = {}
        self.model_initiator.db["name"] = "John"
        self.model_initiator.db["age"] = 33
        self.model_initiator.save_db()
        db_data = None
        with open(self.model_db) as fp:
            db_data = json.load(fp)

        self.assertEqual(db_data, {"name": "John", "age": 33})

        # case 2: non dictionary or array type.
        self.model_initiator.db = "string type"
        rc = self.model_initiator.save_db()
        self.assertFalse(rc)

        # case 3: open with no file. (coverage)
        if os.path.exists(self.model_db_folder):
            shutil.rmtree(self.model_db_folder)

        try:
            self.assertRaises(self.model_initiator.save_db())
        except Exception:
            pass

    @patch("sanji.model_initiator.Thread")
    def test_start_backup_thread_is_not_alive(self, Thread):
        self.model_initiator._backup_thread.is_alive = Mock(return_value=False)
        Thread.return_value = MagicMock(daemon=False, start=Mock())
        self.model_initiator.start_backup()
        self.assertTrue(self.model_initiator._backup_thread.daemon)
        self.model_initiator._backup_thread.start.assert_called_once_with()

    def test_start_backup_thread_is_alive(self):
        with self.assertRaises(RuntimeError):
            self.model_initiator._backup_thread.is_alive =\
                Mock(return_value=True)
            self.model_initiator.start_backup()
        self.model_initiator.stop_backup = Mock()

    def test_stop_backup(self):
        rc = self.model_initiator.stop_backup()
        self.assertFalse(rc)
        self.model_initiator.start_backup()
        rc = self.model_initiator.stop_backup()
        self.assertTrue(rc)

if __name__ == "__main__":
    unittest.main()
