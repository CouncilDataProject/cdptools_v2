#!/usr/bin/env python
# -*- coding: utf-8 -*-


class MissingCredentialsError(Exception):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __str__(self):
        return "Operation not permitted without providing credentials."
