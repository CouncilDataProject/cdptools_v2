#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

import pandas as pd
import pytest

from cdptools.databases import exceptions
from cdptools.databases.database import (
    Database,
    OrderCondition,
    OrderOperators,
    WhereCondition,
    WhereOperators,
)


@pytest.mark.parametrize(
    "filt",
    [
        (("video_uri", "http://video.seattle.gov:8080/media/council/gen_062717V.mp4")),
        (
            (
                "video_uri",
                WhereOperators.eq,
                "http://video.seattle.gov:8080/media/council/gen_062717V.mp4",
            )
        ),
        (["video_uri", "http://video.seattle.gov:8080/media/council/gen_062717V.mp4"]),
        (
            [
                "video_uri",
                WhereOperators.eq,
                "http://video.seattle.gov:8080/media/council/gen_062717V.mp4",
            ]
        ),
        (
            WhereCondition(
                "video_uri",
                WhereOperators.eq,
                "http://video.seattle.gov:8080/media/council/gen_062717V.mp4",
            )
        ),
        pytest.param(
            {"bad", "type"},
            marks=pytest.mark.raises(
                exception=exceptions.UnknownTypeWhereConditionError
            ),
        ),
        pytest.param(
            (1, 2, 3, 4),
            marks=pytest.mark.raises(
                exception=exceptions.UnstructuredWhereConditionError
            ),
        ),
    ],
)
def test_construct_where_condition(filt):
    Database._construct_where_condition(filt)


@pytest.mark.parametrize(
    "order_by",
    [
        (("video_uri")),
        (("video_uri", OrderOperators.desc)),
        (["video_uri"]),
        (["video_uri", OrderOperators.desc]),
        (OrderCondition("video_uri", OrderOperators.desc)),
        pytest.param(
            {"bad", "type"},
            marks=pytest.mark.raises(
                exception=exceptions.UnknownTypeOrderConditionError
            ),
        ),
        pytest.param(
            (1, 2, 3, 4),
            marks=pytest.mark.raises(
                exception=exceptions.UnstructuredOrderConditionError
            ),
        ),
    ],
)
def test_construct_orderby_condition(order_by):
    Database._construct_orderby_condition(order_by)


@pytest.mark.parametrize(
    "rows, table, expected",
    [
        (
            [
                {"event_id": "abcd", "some_value": 1},
                {"event_id": "1234", "some_value": 3},
            ],
            "event",
            {
                "abcd": {"event_id": "abcd", "some_value": 1},
                "1234": {"event_id": "1234", "some_value": 3},
            },
        ),
        ([], "doesnt-matter", {}),
        pytest.param(
            [{"event_id": "abcd", "some_value": 1}],
            "body",
            None,
            marks=pytest.mark.raises(exception=KeyError),
        ),
    ],
)
def test_reshape_list_of_rows_to_dictionary(rows, table, expected):
    actual = Database._reshape_list_of_rows_to_dict(rows, table)
    assert actual == expected


@pytest.mark.parametrize(
    "rows, table, expected",
    [
        (
            [
                {"event_id": "abcd", "some_value": 1},
                {"event_id": "1234", "some_value": 3},
            ],
            None,
            pd.DataFrame(
                [
                    {"event_id": "abcd", "some_value": 1},
                    {"event_id": "1234", "some_value": 3},
                ]
            ),
        ),
        (
            [
                {"event_id": "abcd", "some_value": 1},
                {"event_id": "1234", "some_value": 3},
            ],
            "event",
            pd.DataFrame(
                [
                    {"event_id": "abcd", "some_value": 1},
                    {"event_id": "1234", "some_value": 3},
                ]
            ).set_index("event_id"),
        ),
        ([], None, pd.DataFrame([])),
        pytest.param(
            [{"event_id": "abcd", "some_value": 1}],
            "body",
            None,
            marks=pytest.mark.raises(exception=KeyError),
        ),
    ],
)
def test_reshape_list_of_rows_to_dataframe(rows, table, expected):
    actual = Database._reshape_list_of_rows_to_dataframe(rows, table)
    assert actual.equals(expected)


@pytest.mark.parametrize(
    "value, expected",
    [
        (1, "INTEGER"),
        (1.0, "DOUBLE"),
        ("hello", "STRING"),
        (datetime.utcnow(), "TIMESTAMP"),
        ({"some", "weird", "object"}, "<class 'set'>"),
    ],
)
def test_determine_event_entity_dtype(value, expected):
    actual = Database._determine_event_entity_dtype(value)
    assert actual == expected
