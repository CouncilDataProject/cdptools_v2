#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from cdptools.databases.database import Database, WhereCondition, WhereOperators, OrderCondition, OrderOperators
from cdptools.databases import exceptions


@pytest.mark.parametrize("filt", [
    (("video_uri", "http://video.seattle.gov:8080/media/council/gen_062717V.mp4")),
    (("video_uri", WhereOperators.eq, "http://video.seattle.gov:8080/media/council/gen_062717V.mp4")),
    (["video_uri", "http://video.seattle.gov:8080/media/council/gen_062717V.mp4"]),
    (["video_uri", WhereOperators.eq, "http://video.seattle.gov:8080/media/council/gen_062717V.mp4"]),
    (WhereCondition("video_uri", WhereOperators.eq, "http://video.seattle.gov:8080/media/council/gen_062717V.mp4")),
    pytest.param({"bad", "type"}, marks=pytest.mark.raises(exception=exceptions.UnknownTypeWhereConditionError)),
    pytest.param((1, 2, 3, 4), marks=pytest.mark.raises(exception=exceptions.UnstructuredWhereConditionError))
])
def test_construct_where_condition(filt):
    Database._construct_where_condition(filt)


@pytest.mark.parametrize("order_by", [
    (("video_uri")),
    (("video_uri", OrderOperators.desc)),
    (["video_uri"]),
    (["video_uri", OrderOperators.desc]),
    (OrderCondition("video_uri", OrderOperators.desc)),
    pytest.param({"bad", "type"}, marks=pytest.mark.raises(exception=exceptions.UnknownTypeOrderConditionError)),
    pytest.param((1, 2, 3, 4), marks=pytest.mark.raises(exception=exceptions.UnstructuredOrderConditionError))
])
def test_construct_orderby_condition(order_by):
    Database._construct_orderby_condition(order_by)
