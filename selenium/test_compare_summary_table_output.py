import json
import io
import os.path

import pytest


got_report_summary_filename = 'test_data/got_report_summary.json'
expected_report_summary_filename = 'test_data/expected_report_summary.json'

got_assessment_filename = 'test_data/got_assessment.json'


def test_summary_table_value(table_row, expected_report_table, got_report_table):
    """
    test_summary_table_value is run for every row in the expected & got MHEP report summary
    tables, for example:

    'master | Annual cost by fuel (£) | Standard Tariff'

    It compares the value (e.g. 5234.12) across the expected and got tables.
    """

    try:
        got_value = got_report_table[table_row]
    except KeyError:
        pytest.fail("summary table is missing an expected row: '{}'".format(table_row))

    try:
        expected_value = expected_report_table[table_row]
    except KeyError:
        pytest.fail("summary table had unexpected row: '{}'".format(table_row))

    assert expected_value == got_value


def pytest_generate_tests(metafunc):
    if 'table_row' in metafunc.fixturenames:
        expected = load_expected_report_table()
        got = load_got_report_table()

        all_keys = list(expected.keys()) + list(got.keys())
        metafunc.parametrize('table_row', [i for i in all_keys])


@pytest.fixture()
def expected_report_table(request):
    return load_expected_report_table()


@pytest.fixture()
def got_report_table(request):
    return load_got_report_table()


def load_expected_report_table():
    with io.open(expected_report_summary_filename) as g:
        return json.load(g)


def load_got_report_table():
    """
    load_got_report_table returns the JSON-ified 'MHEP Report Summary Table'

    if the file test_data/got_report_summary.json doesn't exist, it runs the Selenium
    bot to re-generate the assessment and output the table again.
    """
    try:
        with io.open(got_report_summary_filename) as g:
            return json.load(g)
    except IOError:
        print("Did you run `make create_assessment` ?")
        raise
