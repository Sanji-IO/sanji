__test__ = False

import os
import sys
import unittest


try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.config import VersionDict
    from sanji.config import SanjiConfig
except ImportError:
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
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
        pass

    def tearDown(self):
        """
        " Clean up
        """
        pass

    def test_init(self):
        """
        " Test __init__()
        """
        pass

    def test_getitem(self):
        """
        " test __getitem__()
        """
        pass

    def test_setitem(self):
        """
        " test __setitem__()
        """
        pass

    def test_delitem(self):
        pass

    def test_iter(self):
        pass

    def test_len(self):
        pass

    def test_str(self):
        pass

    def test_repr(self):
        pass

    def test_construct_node(self):
        pass

    def test_add_private_node(self):
        pass

    def test_get_private(self):
        pass

    def test_deepcopy(self):
        pass


class TestSanjiConfigClass(unittest.TestCase):
    """
    " Test class
    """

    def setUp(self):
        """
        " Prepare
        """
        pass

    def tearDown(self):
        """
        " Clean up
        """
        pass

    def test_init(self):
        """
        " Test __init__()
        """
        pass

    def test_load(self):
        """
        "
        """
        pass

    def test_save(self):
        """
        "
        """
        pass


if __name__ == "__main__":
    unittest.main()
