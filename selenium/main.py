#!/usr/bin/env python

import json

# from jsondiff import diff
# from pprint import pprint
from collections import OrderedDict

from selenium import webdriver
# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
# from selenium.common.exceptions import ElementNotInteractableException
# from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys


def clear_text(element):
    length = len(element.get_attribute('value'))

    for _ in range(length):
        # element.send_keys(Keys.CONTROL, 'a')
        element.send_keys(Keys.BACKSPACE)
        element.send_keys(Keys.DELETE)
    # TODO : We don't know if we've actually cleared the box with
    #        certainty

    # if len(element.get_attribute('value')) > 0:
    #     raise RuntimeError('failed to clear input box: {}'.format(element.get_attribute("key")))
    # for _ in range (20):
    #     if len(element.get_attribute('value')) == 0:
    #         break
    #     element.send_keys(Keys.DELETE)
    # else:
    #     raise RuntimeError('failed to clear input box: {}', element)


def get_dot_notation(my_dict, scenario_id, key):
    subdata = my_dict

    parts = key.split('.')

    parts[0] = scenario_id   # replace 'data.' with '[scenario_id].'

    for part in parts:
        try:
            subdata = subdata[part]
        except TypeError:   # it's an array, so take the correct item
            subdata = subdata[int(part)]
        except KeyError:
            return None

    if isinstance(subdata, str) or isinstance(subdata, bool):
        return subdata

    if isinstance(subdata, int) or isinstance(subdata, float):
        return str(subdata)


def main():
    with open('test_assessment.json') as json_file:
        test_assessment = json.load(json_file)

    d = webdriver.Firefox()
    d.set_window_position(0, 0)
    d.set_window_size(1480, 1400)

    d.get('http://localhost:8080/emoncms')

    login(d)

    create_assessment(d)

    open_button = d.find_element_by_xpath('//table/tbody/tr[last()]//a')
    open_button.click()

    populate_household_questionnaire(d, test_assessment)
    populate_commentary(d, test_assessment)
    populate_current_energy(d, test_assessment)

    for scenario in ['master']:
        select_scenario(d, scenario)

        populate_ventilation_and_infiltration(d, test_assessment)
        populate_basic_dwelling_data(d, test_assessment)
        populate_fabric(d, test_assessment)
        populate_lighting_appliances_cooking(d, test_assessment)
        populate_heating(d, test_assessment)
        populate_generation(d, test_assessment)

    export_and_diff_assessment(d, test_assessment)


def export_and_diff_assessment(d, expected_assessment):
    click_in_side_menu(d, 'Import/Export', 'Export')
    d.find_element_by_id('show-project-data').click()

    got_json = d.find_element_by_id('export').get_attribute('value')
    got_assessment = json.loads(got_json)

    def sort(od):
        return sorted(od.items(), key=lambda kv: kv[0].upper())

    expected_flattened = sort(flatten_json(expected_assessment))
    got_flattened = sort(flatten_json(got_assessment))

    with open('expected.json', 'w') as f:
        json.dump(expected_assessment, f, indent=4)

    with open('got.json', 'w') as f:
        json.dump(got_assessment, f, indent=4)

    with open('expected.txt', 'w') as f:
        for kv in expected_flattened:
            f.write("{} = {}\n".format(kv[0], kv[1]))

    with open('got.txt', 'w') as f:
        for kv in got_flattened:
            f.write("{} = {}\n".format(kv[0], kv[1]))

    # print("DIFF:")
    # pprint(diff(
    #     expected_flattened,
    #     got_flattened,
    #     syntax='symmetric')
    # )


def populate_lighting_appliances_cooking(d, test_assessment):
    click_in_side_menu(d, 'Lighting, Appliances & Cooking',
                          'Energy use and gains from Lighting, Appliances ' +
                          'and Cooking')

    Select(d.find_element_by_id('LAC_calculation_type')).select_by_value(
      test_assessment["master"]["LAC_calculation_type"]
    )

    check_boxes(d, test_assessment)
    populate_text_fields(d, test_assessment)
    populate_selects(d, test_assessment)


def populate_current_energy(d, test_assessment):
    click_in_side_menu(d, 'Current Energy', 'Current Energy Use')
    fuel_select = d.find_element_by_id('type_of_fuel_select')

    for use in test_assessment["master"]["currentenergy"]["use_by_fuel"]:
        Select(fuel_select).select_by_visible_text(use)
        d.find_element_by_id('add_use_by_fuel').click()


def populate_commentary(d, test_assessment):
    click_in_side_menu(d, 'Commentary', 'Commentary')
    populate_text_fields(d, test_assessment)


def select_scenario(d, scenario_id):
    d.find_element_by_xpath(
            '//div[@scenario="{}"]'.format(scenario_id)
    ).click()


def click_in_side_menu(d, menuLinkLabel, expectedH3):
    print('clicking `{}` and waiting for heading `{}`'.format(
        menuLinkLabel, expectedH3))

    d.find_element_by_link_text(menuLinkLabel).click()
    WebDriverWait(d, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//h3[contains(text(), '" + expectedH3 + "')]")
            )
    )


def populate_fabric(d, test_assessment):
    click_in_side_menu(d, 'Fabric', 'Thermal Mass Parameter (TMP)')

    check_boxes(d, test_assessment)
    populate_text_fields(d, test_assessment)
    populate_selects(d, test_assessment)

    add_fabric_elements(d, test_assessment)


def add_fabric_elements(d, test_assessment):

    def add_element(i, element):
        print('adding {} "{}"'.format(element["type"], element["location"]))

        add_button = d.find_element_by_xpath(
          "//button[contains(@tags, '" + element["type"] + "') and " +
          "contains(@class, 'add-from-lib')]")

        add_button.click()

        d.find_element_by_xpath(
          "//button[@lib='" + element["lib"] + "']").click()

        key = 'fabric.elements.{}'.format(i)
        populate_new_row_selects_and_fields(key, test_assessment, d)

    for index, element in enumerate(
            test_assessment["master"]["fabric"]["elements"]):

        assert index + 1 == element['id'], 'index: {}, element[id]: {}'.format(
                index, element['id'])

        if element['type'] == 'Wall':
            add_element(index, element)

    for index, element in enumerate(
            test_assessment["master"]["fabric"]["elements"]):

        if element['type'] != 'Wall':
            add_element(index, element)


def populate_ventilation_and_infiltration(d, test_assessment):
    test_ventilation_data = test_assessment["master"]["ventilation"]

    click_in_side_menu(d, 'Ventilation and Infiltration', 'Ventilation')

    check_boxes(d, test_assessment)
    populate_selects(d, test_assessment)

    change_system_button = d.find_element_by_xpath(
          "//button[contains(@class, 'add-ventilation-system-from-lib')]")
    ensure_visible(d, change_system_button)
    change_system_button.click()

    system_button = d.find_element_by_xpath(
          "//button[contains(@class, 'add-ventilation-system')]" +
          "[@tag='" + test_ventilation_data["ventilation_tag"] + "']")
    system_button.click()

    add_extract_ventilation_points(d, test_assessment)

    populate_text_fields(d, test_assessment)

    d.find_element_by_xpath('//button[text()="Change system"]').click()
    d.find_element_by_xpath(
      '//button[@tag="' + test_ventilation_data["ventilation_tag"] +
      '" and contains(@class, "add-ventilation-system")]').click()

    add_chimneys_flues_and_fires(d, test_assessment)


def add_chimneys_flues_and_fires(d, test_assessment):
    test_ventilation_data = test_assessment["master"]["ventilation"]

    for i, evp in enumerate(test_ventilation_data["IVF"]):
        d.find_element_by_xpath(
          '//*[text()="Chimneys, open flues and flueless gas fires"]' +
          '/parent::td//button[contains(text(), "Add")]').click()

        d.find_element_by_xpath(
          '//button[@tag="' + evp["tag"] +
          '" and contains(@class, "add-IVF")]').click()

        key = 'ventilation.IVF.{}'.format(i)
        populate_new_row_selects_and_fields(key, test_assessment, d)


def add_extract_ventilation_points(d, test_assessment):
    test_ventilation_data = test_assessment["master"]["ventilation"]

    for i, evp in enumerate(test_ventilation_data["EVP"]):
        d.find_element_by_xpath(
          '//*[text()="Extract ventilation ' +
          'points: intermittent fans and passive vents"]' +
          '/parent::td//button').click()

        d.find_element_by_xpath(
          '//button[@tag="' + evp["tag"] +
          '" and contains(@class, "add-EVP")]').click()

        key = 'ventilation.EVP.{}'.format(i)
        populate_new_row_selects_and_fields(key, test_assessment, d)


def populate_basic_dwelling_data(d, test_assessment):
    click_in_side_menu(d, 'Basic Dwelling Data', 'Context')

    check_boxes(d, test_assessment)
    populate_selects(d, test_assessment)
    populate_text_fields(d, test_assessment)

    add_floors(d, test_assessment)


def add_floors(d, test_assessment):
    for num, floor in enumerate(test_assessment["master"]["floors"]):
        d.find_element_by_id('add-floor').click()
        inputs = d.find_elements_by_xpath(
            '//input[contains(@key, "floors.' + str(num) + '")]')

        for inp in inputs:
            key = inp.get_attribute('key')
            value = get_dot_notation(test_assessment, 'master', key)

            if value is None:
                continue

            inp.clear()
            inp.send_keys(value)


def populate_generation(d, test_assessment):
    d.find_element_by_xpath('//div[@scenario="master"]').click()
    click_in_side_menu(d, 'Generation', 'Generation')

    check_boxes(d, test_assessment)
    populate_text_fields(d, test_assessment)
    populate_selects(d, test_assessment)


def populate_heating(d, test_assessment):
    d.find_element_by_xpath('//div[@scenario="master"]').click()
    click_in_side_menu(d, 'Heating', 'Heating')

    check_boxes(d, test_assessment)
    populate_text_fields(d, test_assessment)
    populate_selects(d, test_assessment)

    add_heating_systems(d, test_assessment)


def add_heating_systems(d, test_assessment):
    for num, heating_system in enumerate(
      test_assessment["master"]["heating_systems"]):

        print('adding heating system: {}'.format(heating_system["name"]))

        d.find_element_by_xpath(
          '//span[contains(@class, "add-heating-system-from-lib")]' +
          '/button').click()

        d.find_element_by_xpath(
          '//button[@tag="' + heating_system["tag"] +
          '" and contains(@class, "add-heating-system")]').click()

        populate_new_row_selects_and_fields('heating_systems.' + str(num),
                                            test_assessment,
                                            d)


def populate_new_row_selects_and_fields(key, test_assessment, d):
    select_keys = [e.get_attribute('key') for e in d.find_elements_by_xpath(
      '//select[contains(@key, "' + key + '")]'
    )]

    if len(select_keys) == 0:
        print('no <select> elements with key {}'.format(key))

    for sel_key in select_keys:
        select = d.find_element_by_xpath('//select[@key="{}"]'.format(sel_key))
        value = get_dot_notation(test_assessment, 'master', sel_key)

        print('[select] key: {}, value: {}'.format(sel_key, value))

        if value is None:
            print('value = None, skipping')
            continue

        ensure_visible(d, select)
        Select(select).select_by_value(value)

    input_keys = [e.get_attribute('key') for e in d.find_elements_by_xpath(
        '//input[(@type="number" or @type="text") and ' +
        'contains(@key, "' + key + '")]' +
        '[not(ancestor::*[contains(@id, "template")])]')]

    if len(input_keys) == 0:
        print('no <input> elements with key {}'.format(key))

    for inp_key in input_keys:
        inp = d.find_element_by_xpath('//input[@key="{}"]'.format(inp_key))
        value = get_dot_notation(test_assessment, 'master', inp_key)

        print('[input] key: {}, value: {}'.format(inp_key, value))

        if value is None:
            continue

        clear_text(inp)
        inp.send_keys(value)


def populate_household_questionnaire(d, test_assessment):
    click_in_side_menu(d, 'Household Questionnaire', 'Basic house data')
    check_boxes(d, test_assessment)
    populate_selects(d, test_assessment)
    populate_text_fields(d, test_assessment)


def ensure_visible(d, element):
    d.execute_script("arguments[0].scrollIntoView(); "
                     "window.scrollBy(0, -500);", element)


def check_boxes(d, test_assessment):
    keys = [e.get_attribute('key') for e in d.find_elements_by_xpath(
      '//input[@key and @type="checkbox"]' +
      '[not(ancestor::*[contains(@id, "template")])]')]

    for key in keys:
        checkbox = d.find_element_by_xpath('//*[@key="{}"]'.format(key))
        value = get_dot_notation(test_assessment, 'master', key)

        if not checkbox.is_displayed():
            print('element not displayed: {}'.format(key))
            continue

        if value is None:
            raise RuntimeError("don't know expected value for {}".format(key))

        alreadyChecked = checkbox.is_selected()

        print('handling checkbox: {}'.format(key))
        print('alreadyChecked: {} required value: {}'.format(alreadyChecked, value))

        if value:
            if not alreadyChecked:
                # ensure_visible(d, checkbox)
                print('ticking checking box')
                checkbox.click()
        else:
            if alreadyChecked:
                # ensure_visible(d, checkbox)
                print('unticking checkbox box')
                checkbox.click()


NON_DISPLAYED_KEYS = set([
    'data.ventilation.dwelling_construction',
    'data.ventilation.suspended_wooden_floor',
    'data.ventilation.balanced_heat_recovery_efficiency',
    'data.ventilation.percentage_draught_proofed',
    'data.ventilation.system_air_change_rate',
    'data.ventilation.system_specific_fan_power',
    'data.appliancelist.list.0.name',
    'data.appliancelist.list.0.category',
    'data.appliancelist.list.0.power',
    'data.appliancelist.list.0.fuel',
    'data.appliancelist.list.0.efficiency',
    'data.appliancelist.list.0.hours',
    'data.appliancelist.list.0.energy',
    'data.appliancelist.list.0.fuel_input',
    'data.generation.solar_annual_kwh',
])


def populate_text_fields(d, test_assessment):
    keys = [e.get_attribute('key') for e in d.find_elements_by_xpath(
      '//input[@key and @type="text"]' +
      '[not(ancestor::*[contains(@id, "template")])] | ' +
      '//textarea[@key]' +
      '[not(ancestor::*[contains(@id, "template")])] | ' +
      '//input[@key and @type="number"]' +
      '[not(ancestor::*[contains(@id, "template")])] | ' +
      '//textarea[@key]' +
      '[not(ancestor::*[contains(@id, "template")])]'
      )]

    for key in keys:
        inp = d.find_element_by_xpath('//*[@key="{}"]'.format(key))
        value = get_dot_notation(test_assessment, 'master', key)

        print("populating: {} with: {}".format(key, value))

        if not inp.is_displayed():
            if key in NON_DISPLAYED_KEYS:
                continue
            else:
                raise RuntimeError("input not displayed for {}".format(key))

        if value is None:
            ignore_keys = set([
                'data.household.3a_heatinghours_weekday_on3_hours',
                'data.household.3a_heatinghours_weekday_on3_mins',
                'data.household.3a_heatinghours_weekday_off3_hours',
                'data.household.3a_heatinghours_weekday_off3_mins',

                'data.household.3a_heatinghours_weekend_on2_hours',
                'data.household.3a_heatinghours_weekend_on2_mins',
                'data.household.3a_heatinghours_weekend_off2_hours',
                'data.household.3a_heatinghours_weekend_off2_mins',

                'data.household.3a_heatinghours_weekend_on3_hours',
                'data.household.3a_heatinghours_weekend_on3_mins',
                'data.household.3a_heatinghours_weekend_off3_hours',
                'data.household.3a_heatinghours_weekend_off3_mins',
            ])
            if key in ignore_keys:
                print("ignoring key: {}".format(key))
                continue
            else:
                raise RuntimeError(
                    "don't know expected value for {}".format(key))

        ensure_visible(d, inp)
        clear_text(inp)
        inp.send_keys(value)


def populate_selects(d, test_assessment):
    keys = [e.get_attribute('key') for e in d.find_elements_by_xpath(
      '//select[@key][not(ancestor::*[contains(@id, "template")])]')]

    for key in keys:
        select = d.find_element_by_xpath('//*[@key="{}"]'.format(key))
        value = get_dot_notation(test_assessment, 'master', key)

        if not select.is_displayed():
            if key in NON_DISPLAYED_KEYS:
                continue
            else:
                raise RuntimeError('element not displayed: {}'.format(key))

        if value is None:
            raise RuntimeError("don't know expected value for {}".format(key))

        try:
            Select(select).select_by_value(value)
        except NoSuchElementException:
            Select(select).select_by_visible_text(value)


def create_assessment(d):
    d.find_element_by_id('new-assessment').click()
    d.find_element_by_id('project-name-input').send_keys('selenium')
    d.find_element_by_id('assessment-create').click()


def login(d):
    username = d.find_element_by_xpath("//input[@name='username']")
    username.send_keys('localadmin')

    password = d.find_element_by_xpath("//input[@name='password']")
    password.send_keys('localadmin')

    login_button = d.find_element_by_id('login')
    login_button.click()


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


if __name__ == '__main__':
    main()
