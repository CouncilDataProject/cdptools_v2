#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import importlib
import logging

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


# def check_system_version(lower: str, target: str) -> bool:
#     """
#     Given two semantic versioning strings, check if
#
#     Parameters
#     ----------
#     module_path: Union[str, List[str]]
#         Python module path or list of path parts to a custom module. Ex: "cptools.pipeline"
#     object_name: str
#         Name of the object to retrieve from the module. Ex: "Pipeline"
#     object_kwargs: Dict
#         Any kwargs to pass to the object.
#
#     Returns
#     -------
#     obj: object
#         The initialized object.
#     """
#     # Convert module path to string
#     if isinstance(module_path, list):
#         module_path = ".".join(module_path)
#
#     # Load target module
#     mod = importlib.import_module(module_path)
#     obj = getattr(mod, object_name)
#     obj = obj(**object_kwargs)
#
#     # Log
#     log.debug(f"Using object: {type(obj)}")
#
#     return obj
