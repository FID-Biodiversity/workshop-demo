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


@pytest.fixture
def spnhc2022_demo_xmi_file_path(test_resource_directory):
    return test_resource_directory / 'reader/spnhc2022-demo.xmi'
