#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Tuple, Union


class MissingCredentialsError(Exception):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __str__(self):
        return "Operation not permitted without providing credentials."


class MissingParameterError(Exception):
    def __init__(self, parameter_options: List[str], **kwargs):
        super().__init__(**kwargs)
        self.parameter_options = parameter_options

    def __str__(self):
        return f"Missing at least one parameter from options: {self.parameter_options}"


class UnstructuredWhereConditionError(Exception):
    def __init__(self, filt: Union[List, Tuple], **kwargs):
        super().__init__(**kwargs)
        self.filt = filt

    def __str__(self):
        return f"WhereCondition's accept at least 2 and at most 3 parameters. Received: {self.filt}"


class UnknownTypeWhereConditionError(Exception):
    def __init__(self, filt: object, **kwargs):
        super().__init__(**kwargs)
        self.filt = filt

    def __str__(self):
        return f"WhereCondition's can be created using list or tuple. Received: {type(self.filt)}, {self.filt}"


class UnstructuredOrderConditionError(Exception):
    def __init__(self, by: Union[List, Tuple], **kwargs):
        super().__init__(**kwargs)
        self.by = by

    def __str__(self):
        return f"OrderCondition's accept at least 1 and at most 2 parameters. Received: {self.by}"


class UnknownTypeOrderConditionError(Exception):
    def __init__(self, by: object, **kwargs):
        super().__init__(**kwargs)
        self.by = by

    def __str__(self):
        return f"OrderCondition's can be created using list, string, or tuple. Received: {type(self.by)}, {self.by}"


class FailedRequestError(Exception):
    def __init__(self, response: str, **kwargs):
        super().__init__(**kwargs)
        self.response = response

    def __str__(self):
        return f"Request failed. Response: {self.response}"


class UniquenessError(Exception):
    def __init__(self, table: str, pks: List[str], results: List[Dict], **kwargs):
        super().__init__(**kwargs)
        self.table = table
        self.pks = pks
        self.results = results

    def __str__(self):
        return f"Table: {self.table}, primary keys: {self.pks} not upheld. Query returned: {self.results}"
