import json

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import ui

from mhep_base_bot import MHEPBaseBot


UNKNOWN_VALUE_KEYS = set([
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

NON_DISPLAYED_KEYS = set([
    'data.ventilation.dwelling_construction',
    'data.ventilation.suspended_wooden_floor',
    'data.ventilation.balanced_heat_recovery_efficiency',
    'data.ventilation.percentage_draught_proofed',
    'data.ventilation.system_air_change_rate',
    'data.ventilation.system_specific_fan_power',
    'data.ventilation.air_permeability_value',

    'data.appliancelist.list.0.name',
    'data.appliancelist.list.0.category',
    'data.appliancelist.list.0.power',
    'data.appliancelist.list.0.fuel',
    'data.appliancelist.list.0.efficiency',
    'data.appliancelist.list.0.hours',
    'data.appliancelist.list.0.energy',
    'data.appliancelist.list.0.fuel_input',
    'data.generation.solar_annual_kwh',

    # Hidden by 'Use PV calculator' being deselected:
    'data.generation.solarpv_kwp_installed',
    'data.generation.solarpv_orientation',
    'data.generation.solarpv_inclination',
    'data.generation.solarpv_overshading',

    'data.generation.solarpv_kwp_installed',
])


class MHEPPopulateBot(MHEPBaseBot):
    def __init__(self, driver):
        super().__init__(driver)

        with open('test_assessment.json') as json_file:
            self.assessment = json.load(json_file)

    def run(self):
        self.d.set_window_position(0, 0)
        self.d.set_window_size(1480, 1400)

        self.d.get('http://localhost:8080/emoncms')

        self.login()
        self.create_assessment('populate and compare')

        self.populate_basic_dwelling_data()  # WORKAROUND: see comment inside function
        self.populate_household_questionnaire()
        self.populate_commentary()
        self.populate_current_energy()

        for scenario in ['master']:
            self.select_scenario(scenario)

            self.populate_ventilation_and_infiltration()
            self.populate_fabric()
            self.populate_lighting_appliances_cooking()
            self.populate_heating()
            self.populate_generation()

    def populate_household_questionnaire(self):
        self.click_in_side_menu('Household Questionnaire', 'Basic house data')
        self.check_boxes()
        self.populate_selects()
        self.populate_text_fields()

    def check_boxes(self):
        keys = [e.get_attribute('key') for e in self.d.find_elements_by_xpath(
          '//input[@key and @type="checkbox"]' +
          '[not(ancestor::*[contains(@id, "template")])]')]

        for key in keys:
            checkbox = self.by_xpath(
                    '//*[@key="{}"]'.format(key))
            value = self.get_dot_notation('master', key)

            if not checkbox.is_displayed():
                print('element not displayed: {}'.format(key))
                continue

            if value is None:
                raise RuntimeError("unknown value for {}".format(key))

            alreadyChecked = checkbox.is_selected()

            print('handling checkbox: {}'.format(key))
            print('alreadyChecked: {} required value: {}'.format(
                alreadyChecked, value))

            if value:
                if not alreadyChecked:
                    print('ticking checking box')
                    checkbox.click()
            else:
                if alreadyChecked:
                    print('unticking checkbox box')
                    checkbox.click()

    def populate_text_fields(self):
        keys = [e.get_attribute('key') for e in self.d.find_elements_by_xpath(
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
            inp = self.by_xpath('//*[@key="{}"]'.format(key))
            value = self.get_dot_notation('master', key)

            print("populating: {} with: {}".format(key, value))

            if not inp.is_displayed():
                if key in NON_DISPLAYED_KEYS:
                    continue
                else:
                    raise RuntimeError("not displayed for {}".format(key))

            if value is None:
                if key in UNKNOWN_VALUE_KEYS:
                    print("ignoring key: {}".format(key))
                    continue
                else:
                    raise RuntimeError(
                        "don't know expected value for {}".format(key))

            self.ensure_visible(inp)
            self.clear_text(inp)
            inp.send_keys(value)

    def populate_selects(self):
        keys = [e.get_attribute('key') for e in self.d.find_elements_by_xpath(
          '//select[@key][not(ancestor::*[contains(@id, "template")])]')]

        for key in keys:
            select = self.by_xpath('//*[@key="{}"]'.format(key))
            value = self.get_dot_notation('master', key)

            if not select.is_displayed():
                if key in NON_DISPLAYED_KEYS:
                    continue
                else:
                    raise RuntimeError('element not displayed: {}'.format(key))

            if value is None:
                raise RuntimeError("unknown value for {}".format(key))

            try:
                ui.Select(select).select_by_value(value)
            except NoSuchElementException:
                ui.Select(select).select_by_visible_text(value)

    def get_dot_notation(self, scenario_id, key):
        subdata = self.assessment

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

    def populate_lighting_appliances_cooking(self):
        self.click_in_side_menu(
                'Lighting, Appliances & Cooking',
                'Energy use and gains from Lighting, Appliances ' +
                'and Cooking')

        ui.Select(
                self.by_id('LAC_calculation_type')
        ).select_by_value(self.assessment["master"]["LAC_calculation_type"])

        self.check_boxes()
        self.populate_text_fields()
        self.populate_selects()

    def populate_current_energy(self):
        self.click_in_side_menu('Current Energy', 'Current Energy Use')
        fuel_select = self.by_id('type_of_fuel_select')

        for use in self.assessment["master"]["currentenergy"]["use_by_fuel"]:
            ui.Select(fuel_select).select_by_visible_text(use)
            self.by_id('add_use_by_fuel').click()

    def populate_commentary(self):
        self.click_in_side_menu('Commentary', 'Commentary')
        self.populate_text_fields()

    def populate_fabric(self):
        self.click_in_side_menu('Fabric', 'Thermal Mass Parameter (TMP)')

        self.check_boxes()
        self.populate_text_fields()
        self.populate_selects()
        self.add_fabric_elements()

    def add_fabric_elements(self):

        def add_element(i, element):
            print('adding {} "{}"'.format(
                element["type"], element["location"]))

            add_button = self.by_xpath(
              "//button[contains(@tags, '" + element["type"] + "') and " +
              "contains(@class, 'add-from-lib')]")

            add_button.click()

            self.by_xpath(
              "//button[@lib='" + element["lib"] + "']").click()

            key = 'fabric.elements.{}'.format(i)
            self.populate_new_row_selects_and_fields(key)

        for index, element in enumerate(
                self.assessment["master"]["fabric"]["elements"]):

            assert index + 1 == element['id'], 'index: {}, element[id]: {}'.format(
                    index, element['id'])

            if element['type'] == 'Wall':
                add_element(index, element)

        for index, element in enumerate(
                self.assessment["master"]["fabric"]["elements"]):

            if element['type'] != 'Wall':
                add_element(index, element)

    def populate_ventilation_and_infiltration(self):
        test_ventilation_data = self.assessment["master"]["ventilation"]

        self.click_in_side_menu('Ventilation and Infiltration', 'Ventilation')

        self.check_boxes()
        self.populate_text_fields()
        self.populate_selects()

        change_system_button = self.by_xpath(
              "//button[contains(@class, 'add-ventilation-system-from-lib')]")
        self.ensure_visible(change_system_button)
        change_system_button.click()

        system_button = self.by_xpath(
              "//button[contains(@class, 'add-ventilation-system')]" +
              "[@tag='" + test_ventilation_data["ventilation_tag"] + "']")
        system_button.click()

        self.add_extract_ventilation_points()

        self.by_xpath('//button[text()="Change system"]').click()
        self.by_xpath(
          '//button[@tag="' + test_ventilation_data["ventilation_tag"] +
          '" and contains(@class, "add-ventilation-system")]').click()

        self.add_chimneys_flues_and_fires()

    def add_chimneys_flues_and_fires(self):
        test_ventilation_data = self.assessment["master"]["ventilation"]

        for i, evp in enumerate(test_ventilation_data["IVF"]):
            self.by_xpath(
              '//*[text()="Chimneys, open flues and flueless gas fires"]' +
              '/parent::td//button[contains(text(), "Add")]').click()

            self.by_xpath(
              '//button[@tag="' + evp["tag"] +
              '" and contains(@class, "add-IVF")]').click()

            key = 'ventilation.IVF.{}'.format(i)
            self.populate_new_row_selects_and_fields(key)

    def add_extract_ventilation_points(self):
        test_ventilation_data = self.assessment["master"]["ventilation"]

        # WORKAROUND: there's a bug in MHEP where adding a heating system breaks the calculations
        # for existing fans, although they're still visible in the UI. Just don't add any fans.
        return
        for i, evp in enumerate(test_ventilation_data["EVP"]):
            self.by_xpath(
              '//*[text()="Extract ventilation ' +
              'points: intermittent fans and passive vents"]' +
              '/parent::td//button').click()

            self.by_xpath(
              '//button[@tag="' + evp["tag"] +
              '" and contains(@class, "add-EVP")]').click()

            key = 'ventilation.EVP.{}'.format(i)
            self.populate_new_row_selects_and_fields(key)

    def populate_basic_dwelling_data(self):
        # WORKAROUND: There's a bug in MHEP which means you can't click the 'Add floors'
        # button if you navigated to "Basic Dwelling Data". The side menu link doesn't load
        # context.js and attach the event.
        # Instead, we have to add floors *immediately* after creating the assessment.
        # click_in_side_menu(d, 'Basic Dwelling Data', 'Context')

        self.await_h3('Context')

        self.check_boxes()
        self.populate_selects()
        self.populate_text_fields()

        self.add_floors()

    def add_floors(self):
        for num, floor in enumerate(self.assessment["master"]["floors"]):
            self.by_id('add-floor').click()
            inputs = self.d.find_elements_by_xpath(
                '//input[contains(@key, "floors.' + str(num) + '")]')

            for inp in inputs:
                key = inp.get_attribute('key')
                value = self.get_dot_notation('master', key)

                if value is None:
                    continue

                inp.clear()
                inp.send_keys(value)

    def populate_generation(self):
        self.by_xpath('//div[@scenario="master"]').click()
        self.click_in_side_menu('Generation', 'Generation')

        self.check_boxes()
        self.populate_text_fields()
        self.populate_selects()

    def populate_heating(self):
        self.by_xpath('//div[@scenario="master"]').click()
        self.click_in_side_menu('Heating', 'Heating')

        self.check_boxes()
        self.populate_text_fields()
        self.populate_selects()

        self.add_heating_systems()

    def add_heating_systems(self):
        for num, heating_system in enumerate(
          self.assessment["master"]["heating_systems"]):

            print('adding heating system: {}'.format(heating_system["name"]))

            self.by_xpath(
              '//span[contains(@class, "add-heating-system-from-lib")]' +
              '/button').click()

            self.by_xpath(
              '//button[@tag="' + heating_system["tag"] +
              '" and contains(@class, "add-heating-system")]').click()

            self.populate_new_row_selects_and_fields('heating_systems.' + str(num)),

    def populate_new_row_selects_and_fields(self, key):
        select_keys = [e.get_attribute('key') for e in self.d.find_elements_by_xpath(
          '//select[contains(@key, "' + key + '")]'
        )]

        if len(select_keys) == 0:
            print('no <select> elements with key {}'.format(key))

        for sel_key in select_keys:
            select = self.by_xpath('//select[@key="{}"]'.format(sel_key))
            value = self.get_dot_notation('master', sel_key)

            print('[select] key: {}, value: {}'.format(sel_key, value))

            if value is None:
                print('value = None, skipping')
                continue

            self.ensure_visible(select)
            ui.Select(select).select_by_value(value)

        input_keys = [e.get_attribute('key') for e in self.d.find_elements_by_xpath(
            '//input[(@type="number" or @type="text") and ' +
            'contains(@key, "' + key + '")]' +
            '[not(ancestor::*[contains(@id, "template")])]')]

        if len(input_keys) == 0:
            print('no <input> elements with key {}'.format(key))

        for inp_key in input_keys:
            inp = self.by_xpath('//input[@key="{}"]'.format(inp_key))
            value = self.get_dot_notation('master', inp_key)

            print('[input] key: {}, value: {}'.format(inp_key, value))

            if value is None:
                continue

            self.clear_text(inp)
            inp.send_keys(value)
