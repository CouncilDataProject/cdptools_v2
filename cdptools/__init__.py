# -*- coding: utf-8 -*-

"""Top-level package for cdptools."""

__author__ = "Jackson Maxfield Brown"
__email__ = "jmaxfieldbrown@gmail.com"
__version__ = "2.0.0"

from .cdp_instances import seattle  # noqa: F401


def get_module_version():
    return __version__
