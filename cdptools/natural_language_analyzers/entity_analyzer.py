#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from itertools import chain, groupby
from typing import Any, Callable, Dict, List, Tuple, Union

import dateparser
import en_core_web_sm
import spacy
from spacy.cli import download

from .nl_analyzer import NLAnalyzer

###############################################################################

MODEL_NAME = "en_core_web_sm"
EntityAnnotator = Callable
AnnotationValueType = Union[str, float, datetime, Any]
EntityAnnotation = Dict[str, AnnotationValueType]

###############################################################################

try:
    spacy.load(MODEL_NAME)
except OSError:
    download(MODEL_NAME)
    spacy.load(MODEL_NAME)

###############################################################################


def _annotate_as_label(label: str) -> EntityAnnotator:
    """
    Creates an annotator that returns the entity annotation as-is with the given annotation label.

    Parameters
    ----------
    label: str
        The label to apply to the generated annotations

    Returns
    -------
    annotator: EntityAnnotator
        An entity annotator which applies the given label
    """

    def annotate(
        entities: spacy.tokens.Span,
        doc: spacy.tokens.Doc,
        event_time: datetime
    ) -> List[EntityAnnotation]:
        """
        Produces annotations consisting of the exact source spacy entity text
        with the given custom annotation label

        Parameters
        ----------
        entities: spacy.tokens.Span
            A list of spacy.tokens.Span objects representing entities
        doc: spacy.tokens.Doc
            The spacy doc the entities are derived from
        event_time: datetime
            The timestamp that the event occurred on

        Returns
        -------
        annotations: List[EntityAnnotation]
            A list of annotations with the given label
        """
        return [_span_to_annotation(e, label, e.text) for e in entities]

    return annotate


def _annotate_empty(
    entities: List[spacy.tokens.Span],
    doc: spacy.tokens.Doc,
    event_time: datetime
) -> List[EntityAnnotation]:
    """
    An Annotator which produces no annotations for the given entities.

    Parameters
    ----------
    entities: List[spacy.tokens.Span]
        A list of spacy.tokens.Span objects representing entities
    doc: spacy.tokens.Doc
        The spacy doc the entities are derived from
    event_time: datetime
        The timestamp that the event occurred on

    Returns
    -------
    annotations: List[EntityAnnotation]
        An empty list.
    """
    return []


def _annotate_person_entities(
    entities: List[spacy.tokens.Span],
    doc: spacy.tokens.Doc,
    event_time: datetime
) -> List[EntityAnnotation]:
    """
    Produce annotations for person entities.

    This filters out entities for ones containing spaces, using that as a proxy
    to indicate first and last name.

    Parameters
    ----------
    entities: List[spacy.tokens.Span]
        A list of spacy.tokens.Span objects representing entities
    doc: spacy.tokens.Doc
        The spacy doc the entities are derived from
    event_time: datetime
        The timestamp that the event occurred on

    Returns
    -------
    annotations: List[EntityAnnotation]
        A list of absolute date annotations.
    """
    return [
        _span_to_annotation(e, "Entity[Person]", e.text)
        for e in entities
        if " " in e.text
    ]


def _annotate_date_entities(
    entities: List[spacy.tokens.Span],
    doc: spacy.tokens.Doc,
    event_time: datetime
) -> List[EntityAnnotation]:
    """
    Parse exact dates and transform relative dates into exact dates based on date and
    time the event ocurred.

    Parameters
    ----------
    entities: List[spacy.tokens.Span]
        A list of spacy.tokens.Span objects representing entities
    doc: spacy.tokens.Doc
        The spacy doc the entities are derived from
    event_time: datetime
        The timestamp that the event occurred on

    Returns
    -------
    annotations: List[EntityAnnotation]
        A list of absolute date annotations.
    """
    base_date = event_time
    conf = {"RELATIVE_BASE": base_date}
    transcribed_dates = []
    for e in entities:
        try:
            parsed_date = dateparser.parse(e.text, settings=conf)
            transcribed_dates.append(
                _span_to_annotation(e, "Entity[Date]", parsed_date)
            )
        except ValueError:
            pass
    return transcribed_dates


def _annotate_money_entities(
    entities: List[spacy.tokens.Span],
    doc: spacy.tokens.Doc,
    event_time: datetime
) -> List[EntityAnnotation]:
    """
    Produces annotations of monetary values.

    Ideally, we'd like to do some additional analysis here to associate those
    dollar amounts back to some expenditure, budget, etc.

    Parameters
    ----------
    entities: List[spacy.tokens.Span]
        A list of spacy.tokens.Span objects representing entities
    doc: spacy.tokens.Doc
        The spacy doc the entities are derived from
    event_time: datetime
        The timestamp that the event occurred on

    Returns
    -------
    annotations: List[EntityAnnotation]
        A list of monetary annotations.
    """
    return [_span_to_annotation(e, "Entity[Money]", e.text) for e in entities]


def _span_to_annotation(
    span: spacy.tokens.Span,
    label: str,
    value: AnnotationValueType
) -> EntityAnnotation:
    """
    Convert a Spacy span to an annotation with the given label and value.

    Parameters
    ----------
    span: spacy.tokens.Span
        The source span for the annotation
    label: str
        A string label to apply to the annotation
    value: AnnotationValueType
        The timestamp that the event occurred on

    Returns
    -------
    annotations: Dict[str, AnnotationValueType]
        A list of monetary annotations.
    """
    return {"start": span.start, "end": span.end, "label": label, "value": value}


class EntityAnalyzer(NLAnalyzer):
    def __init__(self, **kwargs):
        self.NLP = en_core_web_sm.load()
        self._stopwords_by_label = kwargs.get("stopwords_by_label", {})
        self._entity_annotators_by_label = {
            "PERSON": _annotate_person_entities,
            "CARDINAL": _annotate_empty,
            "DATE": _annotate_date_entities,
            "ORG": _annotate_as_label("Entity[Organization]"),
            "GPE": _annotate_as_label("Entity[GPE]"),
            "ORDINAL": _annotate_empty,
            "FAC": _annotate_as_label("Entity[FAC]"),
            "LOC": _annotate_as_label("Entity[Location]"),
            "TIME": _annotate_empty,
            "NORP": _annotate_as_label("Entity[NORP]"),
            "QUANTITY": _annotate_empty,
            "PRODUCT": _annotate_as_label("Entity[Product]"),
            "MONEY": _annotate_money_entities,
            "PERCENT": _annotate_empty,
            "LAW": _annotate_as_label("Entity[Law]"),
            "EVENT": _annotate_as_label("Entity[Event]"),
            "WORK_OF_ART": _annotate_as_label("Entity[WorkOfArt]"),
            "LANGUAGE": _annotate_empty,
        }

    @staticmethod
    def _create_doc(text: str, nlp_model: spacy.LANGUAGE) -> spacy.tokens.Doc:
        """
        Given a spacy NLP model, analyze text, returning a spacy doc.
        """
        return nlp_model(text)

    def _annotate_entities(
        self,
        entities: List[spacy.tokens.Span],
        doc: spacy.tokens.Doc,
        event_time: datetime,
    ) -> Dict[str, List[EntityAnnotation]]:
        """
        Generates a list of annotations for each entity type in a list of entities.

        Parameters
        ----------
        entities: List[spacy.tokens.Span]
            A list of spacy.tokens.Span objects representing entities
        doc: spacy.tokens.Doc
            The spacy doc the entities are derived from
        event_time: datetime
            The timestamp that the event occurred on

        Returns
        -------
        annotations: Dict[str, List[EntityAnnotation]]
            A dict of lists of Annotation objects, keyed by the annotation type
        """
        # Group the extracted entities by entity label
        sorted_entities = sorted(entities, key=lambda e: e.label_)
        grouped_entities = groupby(sorted_entities, key=lambda e: e.label_)
        raw_entities_by_label = {
            entity_type: list(es) for entity_type, es in grouped_entities
        }

        def _filter_by_stopwords(
                entities: List[Spacy.tokens.Span],
                stopwords: List[str]
            ) -> List[Spacy.tokens.Span]:
            """
            Filter entity spans against a stopword list.

            Parameters
            ----------
            entities: List[spacy.tokens.Span]
                A list of spacy.tokens.Span objects representing entities
            stopwords: List[str]
                A list of stopwords

            Returns
            -------
            filtered_entities: List[spacy.tokens.Span]
                The filtered list
            """
            return [e for e in entities if e.text.lower() not in stopwords]

        entities_by_label = {
            entity_type: _filter_by_stopwords(entities, self._stopwords_by_label.get(entity_type, []))
            for entity_type, es in raw_entities_by_label.items())
        }

        # Generate the annotations as appropriate by type
        annotations_by_entity_type = {}
        for entity_type, es in entities_by_label.items():
            entity_type_annotator = self._entity_annotators_by_label[entity_type]
            annotations_by_entity_type[entity_type] = entity_type_annotator(
                es, doc, event_time
            )

        return annotations_by_entity_type

    def load(self, transcript: Dict, event_metadata: Dict) -> Tuple[List[str], datetime]:
        sentences_texts = [sentence["text"] for sentence in transcript["sentences"]]
        return (sentences_texts, event_metadata["event_datetime"])

    def analyze(self, texts: List[str], event_time: datetime) -> List[List[EntityAnnotation]]:
        """
        Generate annotations for a collection of texts related to a single event.

        Parameters
        ----------
        sentence_texts: List[str]
            The list of texts to analyze
        event_time: datetime
            The timestamp that the event occurred on

        Returns
        -------
        sentence_annotations: List[List[EntityAnnotation]]
            A list, where each item is a collection of the annotations associated with the
            corresponding source text.
        """
        docs = (self._create_doc(text, self.NLP) for text in texts)
        doc_annotations_by_entity_type = (
            self._annotate_entities(doc.ents, doc, event_time) for doc in docs
        )
        sentence_annotations = (
            list(chain(doc_annotations.values()))
            for doc_annotations in doc_annotations_by_entity_type
        )
        return list(sentence_annotations)
