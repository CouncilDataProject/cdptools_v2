#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod

###############################################################################


class FileStore(ABC):

    @abstractmethod
    def store_file(self, file: str, **kwargs) -> str:
        """
        Store a file.
        """

        return ""
