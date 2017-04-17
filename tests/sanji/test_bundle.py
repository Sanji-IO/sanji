#!/usr/bin/env python
# -*- coding: UTF-8 -*-

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
    from sanji.bundle import Bundle
    from sanji.bundle import BundleConfigError
except ImportError:
    print("Please check the python PATH for import test module. (%s)"
          % __file__)
    exit(1)

# setup mockup bundle_dir
bundle_dir = os.path.normpath(os.path.realpath(__file__) +
                              './../../mockup/bundle')


class TestBundleClass(unittest.TestCase):

    def setUp(self):
        self.bundle = Bundle(load=False)

    def tearDown(self):
        self.bundle = None

    def test_init(self):
        self.assertIn("sdk_dir", self.bundle.__dict__)
        self.assertIn("bundle_dir", self.bundle.__dict__)
        self.assertIn("profile", self.bundle.__dict__)

        # force load equals to false for testing
        bundle = Bundle(bundle_dir="/123/", sdk_dir="/456/", load=False)
        self.assertEqual(bundle.bundle_dir, "/123/")
        self.assertEqual(bundle.sdk_dir, "/456/")

        # catching BundleConfigError when input bundle path is wrong
        with self.assertRaises(BundleConfigError):
            bundle = Bundle(bundle_dir="/YOU CANT FIND ME/")

        bundle = Bundle(bundle_dir=bundle_dir)
        self.assertEqual(bundle.bundle_dir, bundle_dir)
        json_path = os.path.normpath(os.path.realpath(__file__) +
                                     './../../mockup/bundle/bundle.json')
        with open(json_path) as f:
            self.assertDictEqual(bundle.profile, json.load(f))

    def test_load_json(self):
        with self.assertRaises(BundleConfigError):
            self.bundle.load_json()

if __name__ == "__main__":
    unittest.main()
