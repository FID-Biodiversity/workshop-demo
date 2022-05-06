from typing import List

import pytest

from biofid_demo.reasoner.statistical.proximity import ProximityReasoner, ProximityResult
from biofid_demo.reader import NamedEntity


class TestProximityReasoner:
    def test_proximity_close_named_entities(self, proximity_reasoner, taxa_annotations):
        evaluation_result = proximity_reasoner.evaluate(taxa_annotations)

        expected_annotations = taxa_annotations[:2]
        expected_proximity = 0.91
        assert_annotation_proximity(evaluation_result[0], expected_annotations, expected_proximity)

    def test_proximity_distant_named_entities(self, proximity_reasoner, taxa_annotations):
        evaluation_result = proximity_reasoner.evaluate(taxa_annotations)

        expected_annotations = [taxa_annotations[0], taxa_annotations[3]]
        expected_proximity = 0.0
        assert_annotation_proximity(evaluation_result[2], expected_annotations, expected_proximity)

    def test_proximity_of_multiple_taxa_with_locations(self, proximity_reasoner, taxa_annotations,
                                                       location_annotations):
        evaluation_result = proximity_reasoner.evaluate(taxa_annotations, location_annotations)

        expected_annotations = [taxa_annotations[2], location_annotations[0]]
        expected_proximity = 0.0
        assert_annotation_proximity(evaluation_result[2], expected_annotations, expected_proximity)

        expected_annotations = [taxa_annotations[3], location_annotations[0]]
        expected_proximity = 0.91
        assert_annotation_proximity(evaluation_result[3], expected_annotations, expected_proximity)

    @pytest.fixture
    def proximity_reasoner(self):
        return ProximityReasoner()

    @pytest.fixture
    def taxa_annotations(self):
        return [
            NamedEntity(begin=0, end=15, id='abc', ne_type='taxon',
                        text='Fagus sylvatica', uris=['https://www.example.com/fagus_sylvatica']),
            NamedEntity(begin=100, end=115, id='def', ne_type='taxon',
                        text='Fagus sylvatica', uris=['https://www.example.com/fagus_sylvatica']),
            NamedEntity(begin=116, end=129, id='ghi', ne_type='taxon',
                        text='Procyon lotor', uris=['https://www.example.com/procyon_lotor']),
            NamedEntity(begin=1000, end=1013, id='jkl', ne_type='taxon',
                        text='Taxus baccata', uris=['https://www.example.com/taxus_baccata']),
        ]

    @pytest.fixture
    def location_annotations(self):
        return [
            NamedEntity(begin=1100, end=1109, id='mno', ne_type='location_place',
                        text='Frankfurt', uris=['https://www.example.com/frankfurt_am_main'])
        ]


def assert_annotation_proximity(annotation_proximity_result: ProximityResult,
                                expected_named_entities: List[NamedEntity], expected_proximity):
    assert annotation_proximity_result.annotations == expected_named_entities
    assert annotation_proximity_result.proximity_rate == pytest.approx(expected_proximity, abs=0.005)
