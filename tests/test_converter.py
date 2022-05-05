import pytest

from biofid_demo.converter import extract_text_from_pdf_file


class TestPdfConverter:
    def test_pdf_to_text(self, pdf_file_path):
        text = extract_text_from_pdf_file(pdf_file_path)

        # The \f is a page break indicator
        assert text == 'A test file\n\nIntroduction\n\nAn introduction to text extraction from PDFs.\n\n1\n\n\f'

    @pytest.fixture
    def pdf_file_path(self, test_resource_directory):
        return test_resource_directory / 'converter/test.pdf'

