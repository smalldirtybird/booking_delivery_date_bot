import os
import subprocess
from functools import partial
from random import randrange
from time import sleep

import geckodriver_autoinstaller
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

from clear_temp_folder import clear_temp_folder
from gmail_api import get_verification_code

STATE = 'START'


def human_action_delay(floor, ceil):
    delay_time = randrange(int(floor) * 1000, int(ceil) * 1000) / 1000
    print(f'{delay_time} sec.')
    sleep(delay_time)


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


def start(driver, delay_floor, delay_ceil, ozon_delivery_page_url):
    driver.get(ozon_delivery_page_url)
    human_action_delay(delay_floor, delay_ceil)
    if driver.current_url == ozon_delivery_page_url:
        return 'SWITCH_ACCOUNT'
    if driver.title == 'Just a moment...':
        return 'GOT_CAPTCHA'
    else:
        return 'NEED_AUTHENTICATE'


def start_authenticate(driver, delay_floor, delay_ceil):
    driver.find_element_by_xpath('//span[contains(text(), "Войти")]').click()
    human_action_delay(delay_floor, delay_ceil)
    if driver.title == 'Just a moment...':
        return 'GOT_CAPTCHA'
    else:
        return 'AUTHENTICATION_PROCESS'


def authenticate_with_email(driver, delay_floor, delay_ceil, ozon_login_email,
                            google_credentials, ozon_delivery_page_url):
    driver.find_element_by_xpath(
        '//a[contains(text(), "Войти по почте")]').click()
    human_action_delay(delay_floor, delay_ceil)
    email_field = driver.find_element_by_xpath(
        '//input[contains(@class, "_24-a _24-a3")]')
    for _ in ozon_login_email:
        email_field.send_keys(Keys.BACKSPACE)
    email_field.send_keys(ozon_login_email)
    human_action_delay(delay_floor, delay_ceil)
    driver.find_element_by_xpath(
        '//span[contains(text(), "Получить код")]').click()
    sleep(15)
    human_action_delay(delay_floor, delay_ceil)
    verification_code = get_verification_code(google_credentials)
    driver.find_element_by_xpath(
        '//input[contains(@class, "_24-a _24-a4")]').send_keys(
        verification_code)
    human_action_delay(delay_floor, delay_ceil)
    if driver.current_url == 'https://seller.ozon.ru/app/registration/signin':
        return 'ACCOUNT_SELECTION'
    else:
        driver.get(ozon_delivery_page_url)
    if driver.current_url == ozon_delivery_page_url:
        return 'SWITCH_ACCOUNT'
    if driver.title == 'Just a moment...':
        return 'GOT_CAPTCHA'


def select_account(driver, delay_floor, delay_ceil, account_name,
                   ozon_delivery_page_url):
    driver.find_element_by_xpath(
        f'//div[contains(text(), "{account_name}")]').click()
    human_action_delay(delay_floor, delay_ceil)
    driver.find_element_by_xpath('//span[contains(text(), "Далее")]').click()
    human_action_delay(delay_floor, delay_ceil)
    if driver.current_url == 'https://seller.ozon.ru/app/dashboard/main':
        driver.get(ozon_delivery_page_url)
    if driver.current_url == ozon_delivery_page_url:
        return 'DELIVERY_MANAGEMENT'
    if driver.title == 'Just a moment...':
        return 'GOT_CAPTCHA'


def switch_account(driver, delay_floor, delay_ceil, account_name,
                   ozon_delivery_page_url):
    current_account_button = driver.find_element_by_xpath(
        '//span[contains(@class, '
        '"index_companyItem_Pae1n index_hasSelect_s1JiM")]')
    print(account_name)
    print(current_account_button.text)
    if current_account_button.text == account_name:
        sleep(10)
        return'DELIVERY_MANAGEMENT'
    else:
        current_account_button.click()
        driver.find_element_by_xpath(
            f'//div[contains(text(), "{account_name}")]').click()
        human_action_delay(delay_floor, delay_ceil)
        sleep(10)
        if driver.title == 'Just a moment...':
            return 'GOT_CAPTCHA'
        if driver.current_url == ozon_delivery_page_url:
            return 'DELIVERY_MANAGEMENT'


def handle_captcha(driver, delay_floor, delay_ceil):
    driver.close()
    subprocess.call('./run_browser.sh', shell=True)
    os.system(f'python3 {__file__}')


def handle_statement(driver, ozon_delivery_page_url, delay_floor, delay_ceil,
                     ozon_login_email, google_credentials,
                     account_name):
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
        'DELIVERY_MANAGEMENT': '',
        'GOT_CAPTCHA': handle_captcha,
    }
    STATE = states[STATE](driver, delay_floor, delay_ceil)
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
    account_name = 'ОПТ365'
    with open('run_browser.sh', 'w') as browser_launcher:
        shell_script = f'''#!/bin/bash
        firefox -profile "{profile_path}" --new-tab "{ozon_url}" &
        sleep 10
        pkill  firefox
        '''
        browser_launcher.write(shell_script)

    driver = prepare_webdriver(profile_path)
    while STATE != 'DELIVERY_MANAGEMENT':
        handle_statement(
            driver,
            ozon_delivery_page_url,
            delay_floor,
            delay_ceil,
            ozon_login_email,
            google_credentials,
            account_name,
        )
    driver.close()


if __name__ == '__main__':
    main()
