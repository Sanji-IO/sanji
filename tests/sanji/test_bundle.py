#!/usr/bin/env python
# -*- coding: UTF-8 -*-


import os
import sys
import unittest


try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.bundle import Bundle
    from sanji.bundle import BundleConfigError
except ImportError:
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
    exit(1)


class TestBundleClass(unittest.TestCase):

    def setUp(self):
        self.bundle = Bundle()

    def tearDown(self):
        self.bundle = None

    def test_init(self):
        self.assertIn("sdk_dir", self.bundle.__dict__)
        self.assertIn("bundle_dir", self.bundle.__dict__)
        self.assertIn("profile", self.bundle.__dict__)

        bundle = Bundle(bundle_dir="/123/", sdk_dir="/456/")
        self.assertEqual(bundle.bundle_dir, "/123/")
        self.assertEqual(bundle.sdk_dir, "/456/")

    def test_load_json(self):
        with self.assertRaises(BundleConfigError):
            self.bundle.load_json()

if __name__ == "__main__":
    unittest.main()
