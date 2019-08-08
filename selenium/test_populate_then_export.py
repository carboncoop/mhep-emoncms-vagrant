import json

from pprint import pprint

from selenium import webdriver
from jsondiff import diff

from utils import flatten_json


def test_populate_then_export():
    """
    test_populate_then_export creates a new assessment then interacts with the
    GUI to populate it based on example data. `test_assessment` is an
    assessment exported from MHEP.

    We iterate through input fields in the GUI and look up what to populate
    them with from `test_assessment`

    Finally, we export the new assessment and compare it against expected JSON
    data.
    """

    with open('test_assessment.json') as f:
        test_assessment = json.load(f)

    scraper = PopulateThenExportScraper(webdriver.Firefox(), test_assessment)
    exported_assessment = scraper.run_and_export()
    assert exported_assessment == {}

    def sort(od):
        return sorted(od.items(), key=lambda kv: kv[0].upper())

    expected_flattened = sort(flatten_json(test_assessment))
    exported_flattened = sort(flatten_json(exported_assessment))

    with open('expected.json', 'w') as f:
        json.dump(test_assessment, f, indent=4)

    with open('got.json', 'w') as f:
        json.dump(exported_assessment, f, indent=4)

    with open('expected.txt', 'w') as f:
        for kv in expected_flattened:
            f.write("{} = {}\n".format(kv[0], kv[1]))

    with open('got.txt', 'w') as f:
        for kv in exported_flattened:
            f.write("{} = {}\n".format(kv[0], kv[1]))

    # print("DIFF:")
    # pprint(diff(
    #     expected_flattened,
    #     exported_flattened,
    #     syntax='symmetric')
    # )


class PopulateThenExportScraper():
    def __init__(self, webdriver, test_assessment):
        """
        test_assessment: an example assessment exported from MHEP that we use
        to populate the GUI fields
        """
        self.d = webdriver

    def run_and_export(self):
        self.d.set_window_position(0, 0)
        self.d.set_window_size(1480, 1400)

        self.d.get('http://localhost:8080/emoncms')
        # TODO

        exported_assessment = {}
        return exported_assessment
