__all__ = [
    'NamedEntity'
]

from dataclasses import dataclass
from typing import Protocol, List


@dataclass
class NamedEntity:
    """ A message object holding data about a Named Entity. """
    begin: int
    end: int
    id: str
    ne_type: str
    text: str
    uris: List[str]


class NlpReader(Protocol):
    """ A common interface for all NLP result files. """

    @property
    def taxa(self) -> List[NamedEntity]:
        """ Returns all annotated taxa in the text. """
        ...

    @property
    def locations(self) -> List[NamedEntity]:
        """ Returns all annotated locations in the text. """
        ...

    @property
    def text(self) -> str:
        """ Returns the plain original text. """
        ...

    @property
    def annotated_text(self) -> str:
        """ Returns an annotated representation of the text. """
        ...
