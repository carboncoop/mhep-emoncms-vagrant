import json

from selenium import webdriver

from mhep_populate_bot import MHEPPopulateBot
from test_compare_summary_table_output import (
    got_assessment_filename, got_report_summary_filename
)


def run_bot_save_report_summary_table():
    """
    run_bot_save_report_summary_table creates a new assessment then interacts with the
    GUI to populate it based on example data. `test_assessment` is an
    assessment exported from MHEP.

    We iterate through input fields in the GUI and look up what to populate
    them with from `test_assessment`

    Finally, we parse the 'MHEP Report - summary table' and save it as JSON.
    """

    d = webdriver.Firefox()
    bot = MHEPPopulateBot(d)
    bot.run()

    with open(got_assessment_filename, 'w') as f:
        json.dump(bot.export_assessment(), f, indent=4)

    with open(got_report_summary_filename, 'w') as f:
        json.dump(bot.parse_report_summary_table(), f, indent=4)

    d.quit()


if __name__ == '__main__':
    run_bot_save_report_summary_table()
