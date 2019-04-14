#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
import importlib
import logging
from typing import Dict, List, Union

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger(__file__)

###############################################################################


class Pipeline(ABC):

    @staticmethod
    def load_custom_object(module_path: Union[str, List[str]], object_name: str, object_kwargs: Dict) -> object:
        """
        Load a custom object with kwargs.
        :param module_path: Python path or list of path parts to a custom module. (Ex: "cdptools.pipeline")
        :param object_name: Name of the object from the module. (Ex: "Pipeline")
        :param object_kwargs: Keyword arguments to pass to the object during initialization.
        :return: The initialized object.
        """
        # Convert module path to string
        if isinstance(module_path, list):
            module_path = ".".join(module_path)

        # Load target module
        mod = importlib.import_module(module_path)
        obj = getattr(mod, object_name)
        obj = obj(**object_kwargs)

        # Log
        log.debug(f"Using object: {type(obj)}")

        return obj

    @abstractmethod
    def run(self):
        """
        Run the pipeline.
        """
        pass
