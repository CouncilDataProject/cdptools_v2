#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict
from .doctype import Doctype


class VoteBase(Doctype):
    """
    Abbreviated Vote for nested instances in documents.
    See .vote.py.
    """

    def __init__(
        self,
        vote_decision: str,
        vote_id: str = None,
        person_id: str = None,
        person_name: str = None
    ):
        self._vote_decision = vote_decision
        self._vote_id = vote_id
        self._person_id = person_id
        self._person_name = person_name

    @property
    def vote_decision(self):
        return self._vote_decision

    @property
    def vote_id(self):
        return self._vote_id

    @property
    def person_id(self):
        return self._person_id

    @property
    def person_name(self):
        return self._person_name

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return VoteBase(
            vote_id = source.get("vote_id"),
            person_id = source.get("person_id"),
            person_name = source.get("person_name"),
            vote_decision = source.get("vote_decision")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vote_id": self.vote_id,
            "person_id": self.person_id,
            "person_name": self.person_name,
            "vote_decision": self.vote_decision
        }
