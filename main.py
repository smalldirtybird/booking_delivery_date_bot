import os
import subprocess
from datetime import datetime
from functools import partial
from random import randrange
from time import sleep

import geckodriver_autoinstaller
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

from clear_temp_folder import clear_temp_folder
from gmail_api import get_verification_code
from spreadsheets_api import get_delivery_date_requirements

STATE = 'START'


def human_action_delay(floor, ceil):
    delay_time = randrange(int(floor) * 1000, int(ceil) * 1000) / 1000
    print(f'{delay_time} sec.')
    sleep(delay_time)


def convert_date_range(date_range_string):
    current_year = datetime.now().year
    months_by_numbers = {
        'января': 1,
        'февраля': 2,
        'марта': 3,
        'апреля': 4,
        'мая': 5,
        'июня': 6,
        'июля': 7,
        'августа': 8,
        'сентября': 9,
        'октября': 10,
        'ноября': 11,
        'декабря': 12
    }
    dates = date_range_string.split(sep=' — ')
    date_range = []
    for date in dates:
        day, month = date.split(sep=' ')
        date_string = '.'.join(
            (
                day,
                str(months_by_numbers[month]),
                str(current_year),
            )
        )
        date_range.append(datetime.strptime(date_string, '%d.%m.%Y').date())
    if date_range[0] > date_range[1]:
        date_range[1] += relativedelta(years=+1)
    return tuple(date_range)


def prepare_webdriver(profile_path):
    geckodriver_autoinstaller.install()
    profile = webdriver.FirefoxProfile(profile_path)
    profile.set_preference('dom.webdriver.enabled', False)
    profile.set_preference('useAutomationExtension', False)
    profile.update_preferences()
    desired = DesiredCapabilities.FIREFOX
    options = Options()
    # options.add_argument('--headless')
    driver = webdriver.Firefox(
        firefox_binary='/usr/bin/firefox',
        firefox_profile=profile,
        desired_capabilities=desired,
        options=options,
    )
    return driver


def start(driver, delay, ozon_delivery_page_url):
    driver.get(ozon_delivery_page_url)
    delay()
    if driver.title == 'Just a moment...':
        return 'GOT_CAPTCHA'
    if driver.current_url == ozon_delivery_page_url:
        return 'SWITCH_ACCOUNT'
    else:
        return 'NEED_AUTHENTICATE'


def start_authenticate(driver, delay):
    driver.find_element_by_xpath('//span[contains(text(), "Войти")]').click()
    delay()
    if driver.title == 'Just a moment...':
        return 'GOT_CAPTCHA'
    else:
        return 'AUTHENTICATION_PROCESS'


def authenticate_with_email(driver, delay, ozon_login_email,
                            google_credentials, ozon_delivery_page_url):
    driver.find_element_by_xpath(
        '//a[contains(text(), "Войти по почте")]').click()
    delay()
    email_field = driver.find_element_by_xpath(
        '//input[contains(@class, "_24-a _24-a3")]')
    for _ in ozon_login_email:
        email_field.send_keys(Keys.BACKSPACE)
    email_field.send_keys(ozon_login_email)
    delay()
    driver.find_element_by_xpath(
        '//span[contains(text(), "Получить код")]').click()
    sleep(15)
    delay()
    verification_code = get_verification_code(google_credentials)
    driver.find_element_by_xpath(
        '//input[contains(@class, "_24-a _24-a4")]').send_keys(
        verification_code)
    delay()
    if driver.title == 'Just a moment...':
        return 'GOT_CAPTCHA'
    if driver.current_url == 'https://seller.ozon.ru/app/registration/signin':
        return 'ACCOUNT_SELECTION'
    else:
        driver.get(ozon_delivery_page_url)
    if driver.title == 'Just a moment...':
        return 'GOT_CAPTCHA'
    if driver.current_url == ozon_delivery_page_url:
        return 'SWITCH_ACCOUNT'


def select_account(driver, delay, account_name,
                   ozon_delivery_page_url):
    driver.find_element_by_xpath(
        f'//div[contains(text(), "{account_name}")]').click()
    delay()
    driver.find_element_by_xpath('//span[contains(text(), "Далее")]').click()
    delay()
    if driver.title == 'Just a moment...':
        return 'GOT_CAPTCHA'
    if driver.current_url == 'https://seller.ozon.ru/app/dashboard/main':
        driver.get(ozon_delivery_page_url)
    if driver.current_url == ozon_delivery_page_url:
        return 'DELIVERY_MANAGEMENT'


def switch_account(driver, delay, account_name,
                   ozon_delivery_page_url):
    current_account_button = driver.find_element_by_xpath(
        '//span[contains(@class, '
        '"index_companyItem_Pae1n index_hasSelect_s1JiM")]')
    print(account_name)
    print(current_account_button.text)
    if current_account_button.text == account_name:
        return'DELIVERY_MANAGEMENT'
    else:
        current_account_button.click()
        driver.find_element_by_xpath(
            f'//div[contains(text(), "{account_name}")]').click()
        delay()
        if driver.title == 'Just a moment...':
            return 'GOT_CAPTCHA'
        if driver.current_url == ozon_delivery_page_url:
            return 'DELIVERY_MANAGEMENT'


def change_date_range(driver, delay, desired_date):
    slots_range_switcher = driver.find_element_by_xpath(
        '//div[contains(@class, "slots-range-switcher_dateSwitcher_34ExK")]')
    right_switcher, current_date_range_string,\
        left_switcher = slots_range_switcher.find_elements_by_tag_name('div')
    current_date_range = convert_date_range(current_date_range_string.text)
    print(current_date_range)
    if desired_date < min(current_date_range):
        right_switcher.click()
        delay()
    elif desired_date > max(current_date_range):
        left_switcher.click()
        delay()
    else:
        return
    new_date_range = convert_date_range(driver.find_element_by_xpath(
        '//div[contains(@class, '
        '"slots-range-switcher_dateSwitcherInterval_220Nq")]').text)
    if new_date_range == current_date_range:
        print(new_date_range)
        return
    else:
        change_date_range(driver, delay, desired_date)


def choose_delivery_date(driver, delay, delivery_date_requirements):
    for delivery_id, details in delivery_date_requirements.items():

        # фильтр поставки по номеру
        search_field_button = driver.find_element_by_xpath(
            '//div[contains(text(), "Номер")]')
        search_field_button.click()
        delay()
        delivery_search_field = driver.find_element_by_xpath(
            '//input[contains(@placeholder, "Поиск по номеру поставки")]')
        for _ in delivery_id:
            delivery_search_field.send_keys(Keys.BACKSPACE)
        delivery_search_field.send_keys(delivery_id)
        delay()
        search_field_button.click()
        delay()

        # проверка равенства желаемой и текущей даты поставки
        current_delivery_date_button = driver.find_element_by_xpath(
            '//span[contains(@class, '
            '"orders-table-body-module_dateCell_tKzib")]')
        current_delivery_date = datetime.strptime(
            current_delivery_date_button.text,
            '%d.%m.%Y',
        )
        desired_date = details['min_date']
        if current_delivery_date == desired_date:
            continue

        # поиск максимально близкой к желаемой возможной даты поставки
        current_delivery_date_button.click()
        delay()
        change_date_range(driver, delay, desired_date)
        return 'DONE'


def handle_captcha(driver, delay):
    driver.close()
    delay()
    subprocess.call('./run_browser.sh', shell=True)
    os.system(f'python3 {__file__}')


def handle_statement(driver, ozon_delivery_page_url, delay, ozon_login_email,
                     google_credentials, account_name,
                     delivery_date_requirements):
    global STATE
    states = {
        'START': partial(
            start,
            ozon_delivery_page_url=ozon_delivery_page_url,
        ),
        'NEED_AUTHENTICATE': start_authenticate,
        'AUTHENTICATION_PROCESS': partial(
            authenticate_with_email,
            ozon_login_email=ozon_login_email,
            google_credentials=google_credentials,
            ozon_delivery_page_url=ozon_delivery_page_url,
        ),
        'ACCOUNT_SELECTION': partial(
            select_account,
            account_name=account_name,
            ozon_delivery_page_url=ozon_delivery_page_url
        ),
        'SWITCH_ACCOUNT': partial(
            switch_account,
            account_name=account_name,
            ozon_delivery_page_url=ozon_delivery_page_url,
        ),
        'DELIVERY_MANAGEMENT': partial(
            choose_delivery_date,
            delivery_date_requirements=delivery_date_requirements
        ),
        'GOT_CAPTCHA': handle_captcha,
    }
    STATE = states[STATE](driver, delay)
    print(STATE)


def main():
    clear_temp_folder()
    load_dotenv()
    google_credentials = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    ozon_login_email = os.environ['OZON_LOGIN_EMAIL']
    profile_path = os.environ['FIREFOX_PROFILE_PATH']
    delay_floor = os.environ['ACTION_DELAY_FLOOR']
    delay_ceil = os.environ['ACTION_DELAY_CEIL']
    ozon_url = 'https://seller.ozon.ru'
    ozon_delivery_page_url = 'https://seller.ozon.ru/app/supply/' \
                             'orders?filter=SupplyPreparation'
    account_name = os.environ['ACCOUNT_NAME']
    with open('run_browser.sh', 'w') as browser_launcher:
        shell_script = f'''#!/bin/bash
        firefox -profile "{profile_path}" --new-tab "{ozon_url}" &
        sleep 10
        pkill  firefox
        '''
        browser_launcher.write(shell_script)

    driver = prepare_webdriver(profile_path)
    while STATE != 'DONE':
        handle_statement(
            driver,
            ozon_delivery_page_url,
            partial(human_action_delay, floor=delay_floor, ceil=delay_ceil),
            ozon_login_email,
            google_credentials,
            account_name,
            get_delivery_date_requirements(
                os.environ['GOOGLE_SPREADSHEET_CREDENTIALS'],
                os.environ['TABLE_NAME'],
                os.environ['SHEET_NAME'],
                os.environ['ACCOUNT_NAME'],
            ),
        )
    driver.close()


if __name__ == '__main__':
    main()
