__all__ = [
    'UimaReader',
    'UimaNamedEntities',
    'convert_uima_to_annotated_text'
]

import argparse
import gzip
import html
import itertools
import logging
import pathlib
import re
import urllib
from collections import defaultdict, OrderedDict
from collections.abc import Sequence
from copy import copy
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from functools import partial
from hashlib import md5
from io import BytesIO
from pathlib import Path
from typing import Generator
from typing import Union, List, Tuple, Callable, Optional
from urllib.parse import unquote

from cassis import load_typesystem, load_cas_from_xmi, Cas, TypeSystem
from lxml import etree

from biofid_demo.reader import NamedEntity


class UimaNamedEntities(Enum):
    """ Holds all Named Entity specifications for the BIOfid UIMA data. """
    Taxon = 'org.texttechnologylab.annotation.type.Taxon'
    Location = 'org.texttechnologylab.annotation.type.Location_Place'
    Plant = 'org.texttechnologylab.annotation.type.Plant_Flora'
    Animal = 'org.texttechnologylab.annotation.type.Animal_Fauna'

    def __str__(self):
        return str(self.value)


class UimaReader:
    """ This class enables the reading of XMI files.
        It obeys the NlpReader protocol class.
    """

    ALL_TAXA_CLASSIFIERS = [UimaNamedEntities.Plant, UimaNamedEntities.Animal, UimaNamedEntities.Taxon]
    RELEVANT_ANNOTATIONS = ALL_TAXA_CLASSIFIERS + [UimaNamedEntities.Location]

    def __init__(self, uima_file_path: Union[str, pathlib.Path],
                 typesystem_file_path: Union[str, pathlib.Path] = ''):
        self.uima_file_path = uima_file_path

        if not typesystem_file_path:
            typesystem_file_path = pathlib.Path(__file__).parent / 'resources/default_uima_typesystem.xml'

        self.typesystem = read_typesystem_file(typesystem_file_path)
        self.cas = read_uima_file(self.uima_file_path, self.typesystem)

    @property
    def taxa(self) -> List[NamedEntity]:
        """ Returns all annotated taxa in the text. """
        return [annotation_to_named_entity_object(taxon)
                for taxon in self.iterate_annotations(self.ALL_TAXA_CLASSIFIERS)]

    @property
    def locations(self) -> List[NamedEntity]:
        """ Returns all annotated locations in the text. """
        return [annotation_to_named_entity_object(location)
                for location in self.iterate_annotations(UimaNamedEntities.Location)]

    @property
    def text(self) -> str:
        """ Returns the plain original text. """
        return self.cas.sofa_string

    @property
    def annotated_text(self) -> str:
        """ Returns an annotated representation of the text. """
        return convert_uima_to_annotated_text(self.uima_file_path)

    def iterate_annotations(self, annotation_selector: Union[List[UimaNamedEntities], UimaNamedEntities]) -> Generator:
        """ Iterate all elements of the given selection in the UIMA XML. """
        if not isinstance(annotation_selector, list):
            annotation_selector = [annotation_selector]

        for ne_classifier in annotation_selector:
            for annotation in self.cas.select(str(ne_classifier)):
                yield annotation


def annotation_to_named_entity_object(uima_annotation) -> NamedEntity:
    """ Converts a given UIMA annotation to a NamedEntity object. """
    ne_type = uima_annotation.type.name.split('.')[-1].lower()

    uris = uima_annotation.value
    if uris is not None:
        uris = [unquote(uri.strip()) for uri in uris.split(',')]

    return NamedEntity(
        id=str(uima_annotation.xmiID),
        begin=uima_annotation.begin,
        end=uima_annotation.end,
        text=uima_annotation.get_covered_text(),
        ne_type=ne_type,
        uris=uris
    )


def read_uima_file(uima_file_path: Union[str, pathlib.Path], typesystem: TypeSystem) -> Cas:
    """ Reads a given UIMA file and returns a Cas object with all its data. """
    with open(uima_file_path, 'rb') as f:
        return load_cas_from_xmi(f, typesystem)


def read_typesystem_file(typesystem_file_path: Union[str, pathlib.Path]) -> TypeSystem:
    """ Loads the data from the given typesystem file. """
    with open(typesystem_file_path, 'rb') as f:
        return load_typesystem(f)


NE_LOCATION_STRING = 'location_place'
NE_MISC = 'miscellaneous'
NE_ORGANIZATION = 'organization'
NE_PERSON = 'person_humanbeing'

GENERIC_NAMED_ENTITY_CLASS_INDEX = {
    'loc': NE_LOCATION_STRING,
    'misc': NE_MISC,
    'org': NE_ORGANIZATION,
    'per': NE_PERSON,
}

CONTROL_CHARACTER_REGEX = re.compile(r'&#..;')

# Global variables
CLASS_STRING = 'class'
SUPPORTED_FORMATS = ['xmi', 'xml', 'xmi.gz']
INCLUDE_ID_WITH_TAGS = ['ocrpage', 'sentence']
ANNOTATION_IS_TAG_NAME = ['ocrpage', 'sentence']
SENTENCE = 'sentence'
PAGE = 'ocrpage'
PAGE_ID = 'pageId'
URI = 'uri'
IDENTIFIER = 'identifier'
SENTENCE_TAG = '{http:///de/tudarmstadt/ukp/dkpro/core/api/segmentation/type.ecore}Sentence'
OCR_PAGE_TAG = '{http:///org/texttechnologylab/annotation/ocr.ecore}OCRPage'
SOFA_TAG = '{http:///uima/cas.ecore}Sofa'
TIMEX_TAG = '{http:///de/unihd/dbs/uima/types/heideltime.ecore}Timex3'
TYPE_NAMESPACE = '{http:///org/texttechnologylab/annotation/type.ecore}'
CONCEPT_NAMESPACE = '{http:///org/texttechnologylab/annotation/type/concept.ecore}'
WIKIPEDIA_LINK = '{http:///org/hucompute/textimager/uima/type/wikipedia.ecore}WikipediaLink'
GEONAMES_TAG = '{http:///org/texttechnologylab/annotation.ecore}GeoNamesEntity'
ANNOTATION_COMMENT = '{http:///org/texttechnologylab/annotation.ecore}AnnotationComment'

RELEVANT_TAGS = [SENTENCE_TAG, OCR_PAGE_TAG, SOFA_TAG, TIMEX_TAG, WIKIPEDIA_LINK, GEONAMES_TAG]
EXPECTABLE_ATTRIBUTES = ['pageId', 'timexValue', 'value', 'identifier', 'Target', 'WikiData', 'isInstance', 'id']
EXCLUDE_TAG_NAMES = ['quicktreenode']
PRESERVE_ID_FROM_TAGS = [SENTENCE, PAGE]
VALUE_STRING = 'value'

UTF8_STRING = 'utf-8'

ATTRIBUTE_NORMALIZATION = {
    'Target': 'wikipedia-title',
    'WikiData': 'wikidata-id',
    'identifier': 'biofid-uri'
}

NE_CLASS_PRIORITY = ["Plant_Flora", "Animal_Fauna", "Taxon"]

FLAIR_STRING = 'Flair'
SCORE_STRING = 'score'
MODEL_STRING = 'model'
REMOVED_STRING = '-REMOVED'

HTML_DATA_MODEL_STRING = 'data-probability-model'
HTML_DATA_SCORE_STRING = 'data-probability-score'

PATO_URI_KEY = 'PATO_uri'
PAGE_ID_VALUE_REGEX = r'^.*_(.*)\.xml'


@dataclass
class Attribute:
    """ Holds a single attribute of an XML element. """
    name: str
    identifying_regex: Optional[str] = None
    attribute_key: Optional[str] = None


RELEVANT_ATTRIBUTES = [
    Attribute(name='wikidata', identifying_regex=r'wikidata.org'),  # Wikidata URLs
    Attribute(name='biofid-uri', identifying_regex=r'biofid.de/bio-ontologies'),  # BIOfid URLs
    Attribute(name='wikidata-id', identifying_regex=r'^Q[0-9]+$'),  # only Wikidata ID given
    Attribute(name=PAGE_ID, identifying_regex=PAGE_ID_VALUE_REGEX),  # page id
    Attribute(name=HTML_DATA_SCORE_STRING, attribute_key=SCORE_STRING),  # Model scoring value
    Attribute(name=HTML_DATA_MODEL_STRING, attribute_key=MODEL_STRING),  # Scoring model name
    Attribute(name=URI, identifying_regex=r'^http'),  # Generic URI
    Attribute(name=CLASS_STRING, attribute_key=CLASS_STRING)  # Generic Named Entity Class
]


logger = logging.getLogger(__name__)


def generate_pseudo_tei_from_file(uima_source_file: pathlib.Path) -> str:
    """ Generate a annotated text in pseudo-TEI and returns it.
        The pseudo-TEI does not apply to TEI standards but is just handy.
        :returns: The annotated text as string. Returns None, if the given file does not contain UIMA data or the
        given file format is not supported.
        :rtype: str
    """

    if uima_source_file.name.endswith(tuple(SUPPORTED_FORMATS)):
        file_path = uima_source_file.absolute()

        if file_path.is_file():
            logger.debug('Processing file {}'.format(file_path))

            text = []
            file_object = get_decompressed_file_object(file_path)
            relevant_tags = compile_relevant_entity_tags_and_namespaces(
                                          tags=RELEVANT_TAGS,
                                          namespaces=[TYPE_NAMESPACE, CONCEPT_NAMESPACE]
                                           )

            annotation_list = AnnotationList()
            annotation_callback = partial(process_annotation, annotation_list, text)
            parse_annotation_data(copy(file_object), relevant_tags, annotation_callback)

            if not annotation_list:
                logger.info(f'The file "{file_path}" had not relevant content! -> Skipping!')
                return None

            try:
                text = text[0]
            except IndexError:
                logger.info('No sofaString found in the file {} -> Skipping!'.format(file_path))
                return None

            enrich_annotated_text_with_annotation_comments(annotation_list, file_object)

            # Remove double annotations for single element
            annotation_list = remove_double_annotations(annotation_list)

            return annotate_text(text, annotation_list)
        else:
            return None


def process_annotation(annotation_list, text, elem):
    sofa_string = elem.get('sofaString')
    logger.debug(f'Processing element {elem.tag}')

    if sofa_string is not None:
        # The text of the whole file
        text.append(sofa_string)
    else:
        # A Named Entity
        annotation_list.add(elem)


def compile_relevant_entity_tags_and_namespaces(tags: list = None, namespaces: list = None) -> tuple:
    compiled_result = []
    if tags is not None:
        compiled_result.extend(tags)
    if namespaces is not None:
        namespace_suffix = '*'
        compiled_result.extend(
            namespace if namespace.endswith(namespace_suffix) else f'{namespace}{namespace_suffix}'
            for namespace in namespaces
        )
    return tuple(compiled_result)


def get_settings():
    parser = argparse.ArgumentParser('Convert UIMA XMI to annotated text.')

    parser.add_argument(
        'folder'
    )

    parser.add_argument(
        'sink_dir'
    )

    return parser.parse_args()


def parse_annotation_data(file_object: BytesIO, relevant_tags: Tuple[str], callback: Callable):
    context = etree.iterparse(file_object,
                              tag=relevant_tags,
                              huge_tree=True,
                              recover=False,
                              encoding=UTF8_STRING)

    fast_iter(context, callback)


def fast_iter(context, callback):
    try:
        for event, elem in context:
            callback(elem)
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
    except etree.XMLSyntaxError as ex:
        logger.error(f'The parsing of the file caused an error!\nError Message: {repr(ex)}')

    del context


def enrich_annotated_text_with_annotation_comments(annotation_list: 'AnnotationList', file_object: BytesIO) -> None:

    annotation_comments = {}

    def process_annotation_comment(entity):
        annotation_comments[entity.attrib.get('reference')] = copy(entity.attrib)

    parse_annotation_data(file_object, (ANNOTATION_COMMENT,), process_annotation_comment)

    for annotations_at_position in annotation_list.annotations.values():
        for annotation in annotations_at_position:
            corresponding_comment_data = annotation_comments.get(annotation.id)
            if corresponding_comment_data is not None:
                if corresponding_comment_data.get('key') == PATO_URI_KEY:
                    annotation.attributes[VALUE_STRING] = corresponding_comment_data[VALUE_STRING]


def merge_ne_and_knowledge_entry(annotation_list, knowledge_entries):
    """ Write the URIs to the respective Named Entity. """

    new_start = 0
    for know in knowledge_entries:
        for i, ann in enumerate(annotation_list[new_start:]):
            if ann.begin == know.begin and ann.end == know.end:
                ann.attributes[URI] = know.uri.strip()
                new_start = i
                break

    return annotation_list


def create_tag(pos: int, annotation):
    annotation.name = remove_namespace(annotation.name).lower()

    # Exclude specific annotations
    if annotation.name in EXCLUDE_TAG_NAMES:
        return []

    if annotation.begin == pos:
        return start_tag(annotation)
    else:
        return end_tag(annotation)


def generate_enumerated_key_for_multiple_values(key_name: str, values: list or set) -> dict:
    """ Takes the given key and values and returns a formatted dictionary.
        The key_name is taken as prefix, if the container `values` has more than one element. Hence, when multiple
        elements are given in values, the resulting dictionary will look like this:
        {'key_name-1': value[0], 'key-name-2': value[1]...} .
        If only one value is given, no number is appended to the given key:
        {'key_name': value[0]} .
        If the given container `values` is empty, an empty dictionary is returned.
    """

    number_of_elements_in_values = len(values)
    if number_of_elements_in_values > 1:
        data_to_extend = {f'{key_name}-{index}': values[index] for index in range(0, len(values))}
    elif number_of_elements_in_values == 1:
        data_to_extend = {f'{key_name}': values[0]}
    else:
        data_to_extend = {}

    return data_to_extend


def generate_opening_tag_prefix(annotation: etree.Element) -> str:
    """ Creates an opening tag for the given element. """

    tag = f'<{annotation.name}' if annotation.name in ANNOTATION_IS_TAG_NAME else f'<em'

    if CLASS_STRING not in annotation.attributes:
        tag = f'{tag} class ="{annotation.name}"'

    return tag


def start_tag(annotation: etree.Element) -> str:
    """ Generates a complete start (opening) tag element. """

    tag = generate_opening_tag_prefix(annotation)

    attributes = annotation.attributes

    annotation_id = annotation.id \
        if annotation.name in PRESERVE_ID_FROM_TAGS else md5(annotation.id.encode()).hexdigest()[:10]
    tag = f'{tag} id="{annotation_id}"'

    if attributes:
        for key, value in attributes.items():
            tag = f'{tag} {key}="{value}"'

    if annotation.self_closing:
        tag = f'{tag}/'

    tag = f'{tag}>'

    return tag


def end_tag(annotation):
    if annotation.name not in INCLUDE_ID_WITH_TAGS:
        return '</em>'
    else:
        return '</{}>'.format(annotation.name)


def annotate_text(text, annotation_list):
    full_text = ''
    annotations = annotation_list.get_annotations()
    for pos, char in enumerate(text):
        if pos in annotations:
            for t in resolve_annotation(pos, annotations):
                insert_tags = create_tag(pos, t)
                full_text = f'{full_text}{insert_tags}'

        full_text = f'{full_text}{html.escape(char)}'

    full_text = close_open_ocrpage_tag(full_text)

    return full_text


def resolve_annotation(pos: int, annotation_list: list):
    annotations = annotation_list[pos]
    remove_elements = set()
    wiki_elements = []

    if not annotations:
        return []

    for ann in annotations:
        # Manipulate only start nodes
        if ann.begin == pos:
            ann.attributes = normalize_attributes(ann.attributes)
        lower_name = ann.name.lower()
        if 'other' in lower_name:
            remove_elements.add(ann)
        if 'wikipedialink' in lower_name:
            wiki_elements.append(ann)
            remove_elements.add(ann)

    if len(annotations) == 1:
        if remove_elements:
            # Makes sure no "wikipedialinks" are returned accidentally
            return []
        else:
            return annotations

    for a, b in itertools.combinations(annotations, 2):
        non_intersecting = set(a.attributes) ^ set(b.attributes)
        if a.name == b.name and (a.attributes == b.attributes or 'wikipedia-title' in non_intersecting):
            remove_elements.add(b)
            if a.begin == a.end and a.id == b.id:
                b.self_closing = True

    for e in wiki_elements:
        if 'wikipedia-title' in e.attributes:
            for ann in annotations:
                if remove_namespace(ann.name) not in INCLUDE_ID_WITH_TAGS:
                    ann.attributes['wikipedia-title'] = e.attributes['wikipedia-title']
                    parent = annotation_list[ann.end][annotation_list[ann.end].index(ann)]
                    if parent not in INCLUDE_ID_WITH_TAGS:
                        parent.attributes['wikipedia-title'] = e.attributes['wikipedia-title']

    for e in remove_elements:
        annotations.remove(e)

        end_list = annotation_list[e.end]
        if e.end > pos:
            end_list.remove(e)

    return annotations


def normalize_attributes(attributes):
    found_attributes = defaultdict(list)
    for att in EXPECTABLE_ATTRIBUTES:
        if att in attributes:
            value = urllib.parse.unquote(attributes[att])
            if 'http://' in value and ',' in value or ';' in value:
                # Split a list of URIs and add it to the attributes dictionary
                value = re.split(r',|\t|;', value)
                found_attributes[att].extend(value)
            else:
                # Add a single element to the attributes dictionary
                found_attributes[att].append(value)

    if 'id' in found_attributes:
        geonames_id = found_attributes['id'].pop()
        found_attributes[URI].append(f'https://sws.geonames.org/{geonames_id}/')

    if VALUE_STRING in found_attributes:
        for n in [VALUE_STRING, 'identifier']:
            v = found_attributes.get(n)
            if v is None:
                continue

            scoring_list = [e for e in get_scoring_models_and_values(v)]
            if scoring_list:
                for model_score in scoring_list:
                    found_attributes[HTML_DATA_SCORE_STRING].append(model_score[SCORE_STRING])
                    found_attributes[HTML_DATA_MODEL_STRING].append(model_score[MODEL_STRING])
                continue

            for attribute_value in v:
                lowered_value = attribute_value.lower()
                if 'biofid.de/bio-ontologies' in attribute_value:
                    found_attributes['biofid-uri'].append(attribute_value)
                elif 'wikidata.org' in attribute_value:
                    found_attributes['wikidata'].append(attribute_value)
                elif 'obolibrary.org' in attribute_value:
                    found_attributes[URI].append(attribute_value)
                elif lowered_value in GENERIC_NAMED_ENTITY_CLASS_INDEX:
                    found_attributes[CLASS_STRING].append(GENERIC_NAMED_ENTITY_CLASS_INDEX[lowered_value])

            del found_attributes[n]

    new_attributes = deepcopy(found_attributes)
    for attribute_name, attribute_value in found_attributes.items():
        delete_attribute_after_processing = True
        found_new_value = False
        for attribute in RELEVANT_ATTRIBUTES:
            if attribute.attribute_key is None:
                new_value = get_elements_contain_substring(attribute.identifying_regex, attribute_value)
            elif attribute_name == attribute.name:
                new_value = attribute_value
            else:
                new_value = []
            if new_value:
                if attribute.name == attribute_name:
                    delete_attribute_after_processing = False
                new_attributes[attribute.name] = new_value
                found_new_value = True
            separate_container_values_in_enumerated_attributes(new_attributes, attribute.name)
            if found_new_value:
                break

        if delete_attribute_after_processing:
            del new_attributes[attribute_name]

    if 'Target' in new_attributes:
        new_attributes['wikipedia-title'] = found_attributes['Target']
        del new_attributes['Target']

    if PAGE_ID in new_attributes:
        new_attributes[PAGE_ID] = re.sub(PAGE_ID_VALUE_REGEX, r'\g<1>', new_attributes[PAGE_ID])

    return new_attributes


def remove_double_annotations(annotation_list):
    for ann_set in annotation_list.values():
        if len(ann_set) < 2:
            continue

        remove_elements = set()
        for a1, a2 in itertools.combinations(ann_set, 2):
            if a1.has_same_position(a2):
                priorized_element_name = get_prioritized_element(a1, a2)
                if priorized_element_name:
                    if priorized_element_name == a1.name:
                        remove_elements.add(a2)
                    else:
                        remove_elements.add(a1)
                elif a1.name == a2.name:
                    if len(a1.attributes) > len(a2.attributes):
                        remove_elements.add(a2)
                    else:
                        remove_elements.add(a1)

        ann_set -= remove_elements

    return annotation_list


def get_elements_contain_substring(substring, container, return_container=None):
    if return_container is None:
        return_container = set()

    for elem in container:
        if (isinstance(elem, Sequence) or isinstance(elem, set)) and not isinstance(elem, str):
            return_container = get_elements_contain_substring(substring, elem, return_container)
        elif isinstance(elem, str) and re.search(substring, elem):
            return_container.add(elem)

    return return_container


def get_decompressed_file_object(file_path):
    """ Takes a file path and returns a file-like byte string, if it is a compressed file. """
    logger.debug(f'Unzipping "{file_path}"')

    reading_mode = 'rt'
    if str(file_path).endswith('gz'):
        text = gzip.open(file_path, mode=reading_mode, encoding=UTF8_STRING).read()
    else:
        with open(file_path, reading_mode, encoding=UTF8_STRING) as ifile:
            text = ifile.read()

    text = clean_text(text)

    return BytesIO(bytes(text, UTF8_STRING))


def clean_text(text: str) -> str:
    """ Replaces unwanted characters from the text.
        Replaces characters are:
            - Control characters (e.g. &#10;)
        They are substituted by an appropriate number of spaces.
    """
    return CONTROL_CHARACTER_REGEX.sub(' ', text)


def get_file_stem(file_name: Union[Path, str]) -> str:
    """ Returns only file name without any extensions.
        This even works with multiple extensions.
    """

    extensions = {'txt', 'xml', 'xmi', 'gz'}

    file_name_string = file_name.name if isinstance(file_name, Path) else file_name

    # Yes, this is flawed, but should do the work in the given use case!
    name_substrings_without_extensions = [name_part
                                          for name_part in file_name_string.split('.')
                                          if name_part not in extensions
                                          ]

    return ''.join(name_substrings_without_extensions)


def get_scoring_models_and_values(value: str or list) -> [{str: str}] or []:
    """ Takes a string value and extracts a scoring model and its score from it in a dict list.
        Returns an empty list, if no scoring model and no scoring value could be found.
    """
    if isinstance(value, str) and isinstance(value, list) and isinstance(value, set):
        logger.debug('Wrong type for scoring model value! Returning!')
        return []

    value_list = value.split(';') if isinstance(value, str) else value
    contains_score = any(SCORE_STRING in value_list_element for value_list_element in value_list)

    scoring_list = []
    if contains_score:
        for index, value_list_element in enumerate(value_list):
            if SCORE_STRING in value_list_element:
                # The Scoring model should be given in the position just before the score
                score_model = value_list[index - 1]

                # A model name like `Flair-REMOVED` and its score should be ignored
                if REMOVED_STRING in score_model:
                    continue

                # The scoring value should be given in the form `score=0.12345` or `score = 0.12345`
                score_value = re.search(r'.?([01].[0-9]*)$', value_list_element).group(1)

                # "Round" the given value
                score_value = score_value[:4]

                scoring_list.append({MODEL_STRING: score_model, SCORE_STRING: score_value})

    return scoring_list


def raise_when_empty(container) -> None:
    """ Checks if a given container is empty and raises, if true. """
    if not container:
        raise ValueError('The given directory is empty! Check your configuration!')


def separate_container_values_in_enumerated_attributes(attributes: dict, attribute_name):
    elements_to_add = {}
    attribute_value = attributes.get(attribute_name)
    if attribute_value is None:
        return

    if not isinstance(attribute_value, str) and isinstance(attribute_value, (set, list)):
        container_size = len(attribute_value)
        if container_size > 1:
            for counter, element_value in enumerate(attribute_value):
                elements_to_add[f'{attribute_name}-{counter}'] = element_value

            del attributes[attribute_name]
            attributes.update(elements_to_add)
        elif container_size == 1:
            # Set the single value of the container as attribute value instead of the container
            attributes[attribute_name] = attribute_value.pop()
        else:
            # Mh! Seems like the container is empty => Delete the key!
            del attributes[attribute_name]


def close_open_ocrpage_tag(text: str):
    closing_ocrpage_tag = '</ocrpage>'
    if '<ocrpage>' in text and not text.strip().endswith(closing_ocrpage_tag):
        text = f'{text}{closing_ocrpage_tag}'
    return text


class AnnotationList:

    def __init__(self):
        self.annotations = defaultdict(set)

    def __getitem__(self, item):
        return self.annotations[item]

    def __iter__(self):
        return self.annotations

    def __len__(self):
        return len(self.annotations)

    def values(self):
        return self.annotations.values()

    def add(self, entity):
        try:
            begin = int(entity.get('begin'))
            end = int(entity.get('end'))
        except TypeError:
            return

        if 'value' in entity.attrib:
            if entity.attrib['value'] == remove_namespace(entity.tag):
                return

        annotation = Annotation(entity.get('{http://www.omg.org/XMI}id'), begin, end, entity.tag,
                                deepcopy(entity.attrib))
        text_span_annotations = self.annotations['{}-{}'.format(begin, end)]
        text_span_annotations.add(annotation)

    def get_annotations(self):
        events = defaultdict(list)
        for k, v in self.annotations.items():
            for e in k.split('-'):
                events[int(e)].extend(v)

        return {k: sorted(v, key=lambda x: sort_by_priority_and_position(x, k))
                for k, v in OrderedDict(sorted(events.items())).items()}


def remove_namespace(name):
    return re.sub('^.*?}', '', name)


def get_prioritized_element(elem1_name: str, elem2_name: str) -> str:
    if elem1_name not in NE_CLASS_PRIORITY or elem2_name not in NE_CLASS_PRIORITY:
        return ''

    priorized_element_name = ''
    for ne in NE_CLASS_PRIORITY:
        if ne in elem1_name:
            priorized_element_name = elem1_name
            break
        elif ne in elem2_name:
            priorized_element_name = elem2_name
            break

    return priorized_element_name


class Annotation:
    def __init__(self, id, begin, end, name, attributes):
        self.id = id
        self.begin = begin
        self.end = end
        self.name = name
        self.attributes = attributes
        self.self_closing = False

    def __repr__(self):
        return 'Annotation ID: {} - Begin: {} - End: {} - Name: {} - Attributes {}'.format(
            self.id, self.begin, self.end, self.name, self.attributes
        )

    def __hash__(self):
        return hash(self.begin) + hash(self.end) + hash(self.name)

    def has_same_position(self, other):
        return self.begin == other.begin and self.end == other.end


def sort_by_priority_and_position(elem: Annotation, current_position: int) -> float:
    """ Return a number for sorting the given element.
        The elements are prioritized (when at the same position) by:
            1. Page tags before sentences before words
            2. Closing tags before opening tags
            3. Tags with no content between closing and starting tags.
            4. Tags ending first, come last (they are nested)
    """

    # Page tags come before sentences, which come before words
    if SENTENCE_TAG in elem.name:
        priority_modification = 0.1
    elif OCR_PAGE_TAG in elem.name:
        priority_modification = 0.2
    elif current_position == elem.end:
        priority_modification = 0.3
    else:
        priority_modification = 0.0

    # Close tags before opening new ones
    priority_modification += 0.05 if elem.end == current_position else 0

    # Tags with no content (begin == end), should be between closing and opening tags
    priority_modification -= 0.025 if elem.begin == elem.end else 0

    return current_position - priority_modification


def convert_uima_to_annotated_text(uima_file_path) -> str:
    uima_file_path = pathlib.Path(uima_file_path)
    return generate_pseudo_tei_from_file(uima_file_path)
