import pytest

from biofid_demo.reader import NamedEntity
from biofid_demo.uima import UimaReader


class TestUimaReader:
    def test_get_taxa(self, uima_reader, expected_taxa_named_entities):
        taxa = uima_reader.taxa
        assert taxa == expected_taxa_named_entities

    def test_get_locations(self, uima_reader, expected_locations):
        locations = uima_reader.locations
        assert locations == expected_locations

    def test_get_text(self, uima_reader):
        assert uima_reader.text == 'I found Fagus sylvatica and Taxus baccata.' \
                                   ' Both flowered on a meadow close to Frankfurt and Berlin.'

    @pytest.fixture
    def uima_reader(self, uima_xml_file_path):
        return UimaReader(uima_file_path=uima_xml_file_path)

    @pytest.fixture
    def expected_taxa_named_entities(self):
        return [
            NamedEntity(begin=8, end=23, id='232291', ne_type='taxon',
                        uris=['http://www.wikidata.org/entity/Q32473',
                              'https://www.biofid.de/bio-ontologies#GBIF_1900039'],
                        text='Fagus sylvatica'),
            NamedEntity(begin=28, end=41, id='232300', ne_type='taxon',
                        uris=['http://www.wikidata.org/entity/Q286622',
                              'http://www.wikidata.org/entity/Q50754496',
                              'https://www.biofid.de/bio-ontologies#GBIF_1909334'],
                        text='Taxus baccata')
        ]

    @pytest.fixture
    def expected_locations(self):
        return [
            NamedEntity(begin=78, end=87, id='232305', ne_type='location_place',
                        uris=['http://www.wikidata.org/entity/Q1794'],
                        text='Frankfurt'),
            NamedEntity(begin=92, end=98, id='2024', ne_type='location_place',
                        uris=['https://sws.geonames.org/6547483/'],
                        text='Berlin')
        ]
