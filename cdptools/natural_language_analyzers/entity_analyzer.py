from .nl_analyzer import NLAnalyzer


class EntityAnalyzer(NLAnalyzer):
    def load(self, transcript, event_metadata):
        sentences_texts = [sentence["text"] for sentence in transcript["sentences"]]
        return (sentences_texts, event_metadata["event_datetime"])

    def analyze(self, texts, event_time):
        return [
            {"label": "thing", "value": "stuff"},
            {"label": "person", "value": "George Washington"},
            {"label": "location", "value": "Seattle"}
        ]
