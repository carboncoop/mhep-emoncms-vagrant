from os.path import abspath, dirname, join

from selenium import webdriver

from utils import (
        create_assessment,
        click_in_side_menu,
        login,
        parse_report_summary_table,
    )


def test_import_then_read_back():
    assessment_filename = abspath(
            join(dirname(__file__), 'test_assessment.json')
    )

    scraper = ImportThenReadBackScraper(assessment_filename)
    scraper.run()


class ImportThenReadBackScraper():
    def __init__(self, assessment_filename):
        """
        test_assessment: an example assessment exported from MHEP that we use
        to populate the GUI fields
        """
        self.d = webdriver.Firefox()
        self.assessment_filename = assessment_filename

    def run(self):
        self.d.set_window_position(0, 0)
        self.d.set_window_size(1480, 1400)

        self.d.get('http://localhost:8080/emoncms')
        login(self.d)
        create_assessment(self.d, 'imported from JSON')
        click_in_side_menu(self.d, 'Import/Export', 'Import')

        self.d.find_element_by_id('file_to_upload').send_keys(
                self.assessment_filename
        )
        self.d.find_element_by_xpath('//input[@value="Import file"]').click()

        summary = parse_report_summary_table(self.d)
        import io
        import json
        with io.open('test_data/expected_summary.json', 'w') as f:
            json.dump(summary, f, indent=4)
