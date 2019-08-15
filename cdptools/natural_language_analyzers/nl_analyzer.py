from abc import ABC, abstractmethod


class NLAnalyzer(ABC):
    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def analyze(self):
        pass
