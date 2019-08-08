import datetime
import json

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from utils import flatten_summary_table


class MHEPBaseBot():
    def __init__(self, webdriver):
        self.d = webdriver

    def create_assessment(self, name):
        assessment_name = 'selenium_{}: {}'.format(
            datetime.datetime.now().replace(microsecond=0).isoformat(),
            name
        )

        self.by_id('new-assessment').click()
        self.by_id('project-name-input').send_keys(assessment_name)
        self.by_id('assessment-create').click()

        open_button = self.by_xpath('//table/tbody/tr[last()]//a')
        open_button.click()

    def login(self):
        username = self.d.find_element_by_xpath("//input[@name='username']")
        username.send_keys('localadmin')

        password = self.d.find_element_by_xpath("//input[@name='password']")
        password.send_keys('localadmin')

        login_button = self.d.find_element_by_id('login')
        login_button.click()

    def ensure_visible(self, element):
        self.d.execute_script("arguments[0].scrollIntoView(); "
                              "window.scrollBy(0, -500);", element)

    def click_in_side_menu(self, menuLinkLabel, expectedH3):
        print('clicking `{}` and waiting for heading `{}`'.format(
            menuLinkLabel, expectedH3))

        button = self.d.find_element_by_link_text(menuLinkLabel)
        self.ensure_visible(button)
        button.click()

        WebDriverWait(self.d, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//h3[contains(text(), '" + expectedH3 + "')]")
                )
        )

    def select_scenario(self, scenario_id):
        self.d.find_element_by_xpath(
                '//div[@scenario="{}"]'.format(scenario_id)
        ).click()

    def clear_text(self, element):
        length = len(element.get_attribute('value'))

        for _ in range(length):
            element.send_keys(Keys.BACKSPACE)
            element.send_keys(Keys.DELETE)

    def export_assessment(self):
        self.click_in_side_menu('Import/Export', 'Export')
        self.d.find_element_by_id('show-project-data').click()

        got_json = self.d.find_element_by_id('export').get_attribute('value')
        return json.loads(got_json)

    def parse_report_summary_table(self):
        self.click_in_side_menu('MHEP Report', 'Summary table')
        table_html = self.d.find_element_by_id('summary').get_attribute("outerHTML")
        return flatten_summary_table(table_html)

    def by_xpath(self, *args, **kwargs):
        return self.d.find_element_by_xpath(*args, **kwargs)

    def by_id(self, *args, **kwargs):
        return self.d.find_element_by_id(*args, **kwargs)
