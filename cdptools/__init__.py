# -*- coding: utf-8 -*-

"""Top-level package for cdptools."""

__author__ = "Jackson Maxfield Brown"
__email__ = "jmaxfieldbrown@gmail.com"
__version__ = "2.0.1"

from .cdp_instance import CDPInstance  # noqa: F401


def get_module_version():
    return __version__
