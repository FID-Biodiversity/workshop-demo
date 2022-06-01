__all__ = [
    'NamedEntity'
]

from dataclasses import dataclass
from typing import List
from abc import ABC, abstractmethod


@dataclass
class NamedEntity:
    """ A message object holding data about a Named Entity. """
    begin: int
    end: int
    id: str
    ne_type: str
    text: str
    uris: List[str]

    def __hash__(self):
        return hash((self.begin, self.end, self.id))


class NlpReader(ABC):
    """ A common interface for all NLP result files. """

    @property
    @abstractmethod
    def taxa(self) -> List[NamedEntity]:
        """ Returns all annotated taxa in the text. """
        ...

    @property
    @abstractmethod
    def locations(self) -> List[NamedEntity]:
        """ Returns all annotated locations in the text. """
        ...

    @property
    @abstractmethod
    def text(self) -> str:
        """ Returns the plain original text. """
        ...

    @property
    @abstractmethod
    def annotated_text(self) -> str:
        """ Returns an annotated representation of the text. """
        ...
