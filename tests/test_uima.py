from biofid_demo.uima import convert_uima_to_annotated_text


class TestUimaConversion:
    def test_convert_uima_to_annotated_text(self, uima_xml_file_path):
        annotated_text = convert_uima_to_annotated_text(uima_xml_file_path)
        assert annotated_text == '<sentence class ="sentence" id="19">I found <em class ="taxon" id="652a3cabc6" ' \
                                 'wikidata="http://www.wikidata.org/entity/Q32473" biofid-uri="' \
                                 'https://www.biofid.de/bio-ontologies#GBIF_1900039">Fagus sylvatica</em> and <em ' \
                                 'class ="taxon" id="cc95270887" biofid-uri="' \
                                 'https://www.biofid.de/bio-ontologies#GBIF_1909334" wikidata-0="' \
                                 'http://www.wikidata.org/entity/Q286622" ' \
                                 'wikidata-1="http://www.wikidata.org/entity/Q50754496">Taxus baccata</em>.</sentence> ' \
                                 '<sentence class ="sentence" id="31">Both flowered on a meadow close to <em class ' \
                                 '="location_place" id="7982b06819" ' \
                                 'wikidata="http://www.wikidata.org/entity/Q1794">Frankfurt</em>.'
