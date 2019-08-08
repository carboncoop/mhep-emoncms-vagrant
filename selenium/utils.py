import datetime
from collections import OrderedDict
import lxml.html

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


def flatten_json(nested_json):
    """
        Flatten json object with nested keys into a single level.
        Args:
            nested_json: A nested json object.
        Returns:
            The flattened json object if successful, None otherwise.
    """
    out = OrderedDict()

    def flatten(x, name=''):
        if type(x) is dict:
            for key in x:
                flatten(x[key], name + '.' + key)
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + '[' + str(i) + ']')
                i += 1
        else:
            out[name[1:]] = x

    flatten(nested_json)
    return out


def login(d):
    username = d.find_element_by_xpath("//input[@name='username']")
    username.send_keys('localadmin')

    password = d.find_element_by_xpath("//input[@name='password']")
    password.send_keys('localadmin')

    login_button = d.find_element_by_id('login')
    login_button.click()


def create_assessment(d, name):
    assessment_name = 'selenium_{}: {}'.format(
        datetime.datetime.now().replace(microsecond=0).isoformat(),
        name
    )

    d.find_element_by_id('new-assessment').click()
    d.find_element_by_id('project-name-input').send_keys(assessment_name)
    d.find_element_by_id('assessment-create').click()

    open_button = d.find_element_by_xpath('//table/tbody/tr[last()]//a')
    open_button.click()


def click_in_side_menu(d, menuLinkLabel, expectedH3):
    print('clicking `{}` and waiting for heading `{}`'.format(
        menuLinkLabel, expectedH3))

    d.find_element_by_link_text(menuLinkLabel).click()
    WebDriverWait(d, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//h3[contains(text(), '" + expectedH3 + "')]")
            )
    )


def parse_report_summary_table(d):
    click_in_side_menu(d, 'MHEP Report', 'Summary table')
    table_html = d.find_element_by_id('summary').get_attribute("outerHTML")
    return flatten_summary_table(table_html)


def flatten_summary_table(html):
    root = lxml.html.fromstring(html)

    scenarios = [s.text for s in root.xpath('//th')[1:]]
    # scenarios is e.g. ['master', 'scenario1']

    print(scenarios)

    section_name = 'NOSECTION'

    out = OrderedDict()

    for tr in root.xpath('//table//tr')[1:]:

        cols = [td.text_content().strip() for td in tr.xpath('./td')]

        if all(c == '' for c in cols):  # skip blank row
            continue

        if is_section_row(cols):
            section_name = cols[0]
        else:
            # e.g. ["heating demand", "1.2", '3.4']
            data_key, data_values = cols[0], cols[1:]

            for scenario, data_value in zip(scenarios, data_values):
                key = '{} | {} | {}'.format(scenario, section_name, data_key)
                value = data_value

                out[key] = value

    from pprint import pprint
    pprint(out)
    return out


def is_section_row(columns):
    """
    return True if the first column has text and the remaining n are empty

    e.g. ['Totals', '', ''] # this is a section row

    comes from a row like this:
    <tr>
      <td><b>Totals</b></td>
      <td></td>
      <td></td>
    </tr>
    """

    return columns[0] != '' and all(column == '' for column in columns[1:])
