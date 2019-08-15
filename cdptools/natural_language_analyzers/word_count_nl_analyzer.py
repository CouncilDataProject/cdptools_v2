import re

from .nl_analyzer import NLAnalyzer

_WHITESPACE = re.compile(r"\s+")


class WordCountNLAnalyzer(NLAnalyzer):
    @staticmethod
    def _naive_word_count(text):
        if not text or _WHITESPACE.sub(text, "") == 0:
            return 0

        return len(text.split(" "))

    def _count_words(self, text):
        return self._naive_word_count(text)

    def load(self, transcript):
        return transcript["full_text"]

    def analyze(self, text):
        return {"word_count": self._count_words(text)}
