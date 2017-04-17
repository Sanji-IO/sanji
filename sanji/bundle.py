#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import simplejson as json
import logging

_logger = logging.getLogger("sanji.sdk.bundle")


class Bundle(object):

    def __init__(self,
                 bundle_dir=os.getenv("BUNDLE_DIR", os.getcwd()),
                 sdk_dir=os.path.dirname(os.path.realpath(__file__)),
                 load=True):
        self.sdk_dir = sdk_dir
        self.bundle_dir = bundle_dir
        self.profile = None
        if load is True:
            self.load_json()

    def load_json(self):
        json_path = os.path.join(self.bundle_dir, "bundle.json")
        try:
            with open(json_path) as f:
                self.profile = json.load(f)
        except Exception as e:
            raise BundleConfigError("Can't load file: %s, error: %s",
                                    (json_path, str(e)))

        _logger.debug("Model: %s config has been loaded." %
                      (self.profile["name"],))


class BundleConfigError(Exception):
    pass
