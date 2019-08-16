from datetime import datetime as dt
from itertools import chain, groupby

from typing import Any, Callable, List, Union
import dateparser
import en_core_web_sm
import spacy
from spacy import displacy

from .nl_analyzer import NLAnalyzer


def _annotate_as_label(label):
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

    def annotate(entities, doc, event_time):
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
            annotations
                A list of annotations with the given label
        """
        return [_span_to_annotation(e, label, e.text) for e in entities]

    return annotate


def _annotate_empty(entities, doc, event_time):
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
        annotations
            An empty list.
    """
    return []


def _annotate_person_entities(entities, doc, event):
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
        annotations
            A list of absolute date annotations.
    """
    filtered = [
        _span_to_annotation(e, "Entity[Person]", e.text)
        for e in entities
        if " " in e.text
    ]
    return filtered


def _annotate_date_entities(entities, doc, event_time):
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
        annotations
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


def _annotate_product_entities(entities, doc, event_time):
    """
        Produces annotations of product names, removing commong false positives.

        False positives removed:
            - "amendment"

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
        annotations
            A list of product entity annotations
    """
    filtered = [e for e in entities if e.text.lower() != "amendment"]
    return [_span_to_annotation(e, "Entity[Product]", e.text) for e in filtered]


def _annotate_money_entities(entities, doc, event_time):
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
        annotations
            A list of monetary annotations.
    """
    return [_span_to_annotation(e, "Entity[Money]", e.text) for e in entities]


def _span_to_annotation(span, label, value):
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
        annotations
            A list of monetary annotations.
    """
    return {"start": span.start, "end": span.end, "label": label, "value": value}


class EntityAnalyzer(NLAnalyzer):
    def __init__(self):
        self.NLP = en_core_web_sm.load()
        self._entity_annotators_by_type = {
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
            "PRODUCT": _annotate_product_entities,
            "MONEY": _annotate_money_entities,
            "PERCENT": _annotate_empty,
            "LAW": _annotate_as_label("Entity[Law]"),
            "EVENT": _annotate_as_label("Entity[Event]"),
            "WORK_OF_ART": _annotate_as_label("Entity[WorkOfArt]"),
            "LANGUAGE": _annotate_empty,
        }

    @staticmethod
    def _create_doc(text, nlp_model):
        """
        Given a spacy NLP model, analyze text, returning a spacy doc.
        """
        return nlp_model(text)

    def _annotate_entities(self, entities, doc, event_time):
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
            annotations
                A dict of lists of Annotation objects, keyed by the annotation type
        """
        # Group the extracted entities by entity label
        sorted_entities = sorted(entities, key=lambda e: e.label_)
        grouped_entities = groupby(sorted_entities, key=lambda e: e.label_)
        entities_by_type = {
            entity_type: list(es) for entity_type, es in grouped_entities
        }

        # Generate the annotations as appropriate by type
        annotations_by_entity_type = {}
        for entity_type, es in entities_by_type.items():
            entity_type_annotator = self._entity_annotators_by_type[entity_type]
            annotations_by_entity_type[entity_type] = entity_type_annotator(
                es, doc, event_time
            )

        return annotations_by_entity_type

    def load(self, transcript, event_metadata):
        sentences_texts = [sentence["text"] for sentence in transcript["sentences"]]
        return (sentences_texts, event_metadata["event_datetime"])

    def analyze(self, texts, event_time):
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
            sentence_annotations
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

