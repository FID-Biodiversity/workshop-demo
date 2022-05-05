__all__ = [
    'AnnotationData',
]

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List


class AnnotationType(Enum):
    Taxon = 'taxon'
    Location = 'location'

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return str(self) == str(other)


@dataclass
class AnnotationData:
    """ Holds generic data necessary for text annotation. """
    begin: int
    end: int
    id: str
    ne_type: str
    annotation_type: AnnotationType
    text: str
    uris: List[str]


class AnnotationSchema(ABC):
    """ A common base for text annotation schemas. """
    def __init__(self, original_text: str, annotation_data: List[AnnotationData]):
        self.text = original_text
        self.annotations = annotation_data

    @property
    @abstractmethod
    def annotated_text(self) -> str:
        """ Returns the fully annotated text string. """
        pass


class PseudoTei(AnnotationSchema):
    """ Applies an annotation schema that borrows from TEI.
        Example:
            <em id="fzds735" class="taxon" uri-0="http://www.foo.com/1234" uri-1="http://www.bar.com/1234">Foo</em>
    """

    @property
    def annotated_text(self) -> str:
        pass

