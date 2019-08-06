#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Union

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class Pipeline(ABC):

    @staticmethod
    def load_custom_object(module_path: Union[str, List[str]], object_name: str, object_kwargs: Dict) -> object:
        """
        Load a custom object with kwargs.

        Parameters
        ----------
        module_path: Union[str, List[str]]
            Python module path or list of path parts to a custom module. Ex: "cptools.pipeline"
        object_name: str
            Name of the object to retrieve from the module. Ex: "Pipeline"
        object_kwargs: Dict
            Any kwargs to pass to the object.

        Returns
        -------
        obj: object
            The initialized object.
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


class ValuesForTerm:
    """
    Used for multithreaded uploaded of index terms.
    Can't use NamedTuple here because dictionaries are mutuable.
    """

    def __init__(self, term: str, values: Dict[str, float]):
        self.term = term
        self.values = values
