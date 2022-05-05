import pathlib

import pytest


@pytest.fixture
def test_directory():
    return pathlib.Path(__file__).parent


@pytest.fixture
def test_resource_directory(test_directory):
    return test_directory / 'resources'


@pytest.fixture
def uima_xml_file_path(test_resource_directory):
    return test_resource_directory / 'reader/uima.xml'
