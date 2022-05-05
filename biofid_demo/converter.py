__all__ = [
    'extract_text_from_pdf_file'
]

import pathlib
from typing import Union

from pdfminer.high_level import extract_text


def extract_text_from_pdf_file(pdf_file_path: Union[str, pathlib.Path], password: str = '') -> str:
    """ Extract the text from the given PDF file.
        This function does NOT imply OCR! The provided PDF file has to include the text already!
        If the PDF is encrypted with a password, you may give it with the `password` parameter.
    """
    text = extract_text(pdf_file_path, password=password)
    return text
