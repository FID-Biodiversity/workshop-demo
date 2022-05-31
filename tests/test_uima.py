import re

from biofid_demo.uima import convert_uima_to_annotated_text


class TestUimaConversion:
    def test_convert_uima_to_annotated_text(self, uima_xml_file_path):
        annotated_text = convert_uima_to_annotated_text(uima_xml_file_path)
        assert annotated_text == '<sentence class="sentence" id="19">I found <em class="taxon" id="652a3cabc6" ' \
                                 'wikidata="http://www.wikidata.org/entity/Q32473" biofid-uri="' \
                                 'https://www.biofid.de/bio-ontologies#GBIF_1900039">Fagus sylvatica</em> and <em ' \
                                 'class="taxon" id="cc95270887" biofid-uri="' \
                                 'https://www.biofid.de/bio-ontologies#GBIF_1909334" wikidata-0="' \
                                 'http://www.wikidata.org/entity/Q286622" ' \
                                 'wikidata-1="http://www.wikidata.org/entity/Q50754496">Taxus baccata</em>.</sentence> ' \
                                 '<sentence class="sentence" id="31">Both flowered on a meadow close to <em class' \
                                 '="location_place" id="7982b06819" ' \
                                 'wikidata="http://www.wikidata.org/entity/Q1794">Frankfurt</em> and <em ' \
                                 'class="location_place" id="07811dc6c4" ' \
                                 'uri="https://sws.geonames.org/6547483/">Berlin</em>.'

    def test_processing_spnhc2022_demo_xmi(self, spnhc2022_demo_xmi_file_path):
        annotated_text = convert_uima_to_annotated_text(spnhc2022_demo_xmi_file_path)
        assert_em_tag_in_text(text_to_check=annotated_text,
                              class_name='location_place', arguments={'uri': 'https://sws.geonames.org/3220968/'},
                              annotated_text='Frankfurt')
        assert_em_tag_in_text(text_to_check=annotated_text,
                              class_name='taxon', arguments={'wikidata': 'http://www.wikidata.org/entity/Q5113'},
                              annotated_text='Vögel')


def assert_em_tag_in_text(text_to_check: str, class_name: str = None, arguments: dict = None,
                          annotated_text: str = None):
    class_name = class_name if class_name is not None else r'\w+?'
    annotated_text = annotated_text if annotated_text is not None else '.*?'
    if arguments is not None:
        arguments = [fr'{key}="{value}"' for key, value in arguments.items()]

    regex_string = fr'<em class=\"{class_name}\".*?>{annotated_text}</em>'
    relevant_text_match = re.search(regex_string, text_to_check, re.MULTILINE)
    assert relevant_text_match is not None

    # Check that the provided arguments are in the given string
    if arguments is not None:
        text_string = relevant_text_match.group()
        for arg in arguments:
            assert arg in text_string
