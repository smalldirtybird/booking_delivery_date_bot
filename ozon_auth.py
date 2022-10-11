import os
import pickle
import subprocess
from functools import partial
from random import randrange
from time import sleep

import geckodriver_autoinstaller
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

from clear_temp_folder import clear_temp_folder
from gmail_api import get_verification_code


class CaptchaReceived(Exception):
    def __init__(self, text):
        self.text = text


def human_action_delay(floor, ceil):
    delay_time = randrange(int(floor) * 1000, int(ceil) * 1000) / 1000
    print(delay_time)
    sleep(delay_time)


def prepare_webdriver(profile_path):
    geckodriver_autoinstaller.install()
    profile = webdriver.FirefoxProfile(profile_path)
    profile.set_preference('dom.webdriver.enabled', False)
    profile.set_preference('useAutomationExtension', False)
    profile.update_preferences()
    desired = DesiredCapabilities.FIREFOX
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Firefox(
        firefox_profile=profile,
        desired_capabilities=desired,
        options=options,
    )
    return driver


def pass_to_main_page(driver, ozon_url):
    url = ozon_url
    driver.get(url)


def push_main_page_enter_button(driver):
    enter_button = driver.find_element(
        By.XPATH,
        '//div[3]/a',
    )
    enter_button.click()


def push_enter_ozon_id_button(driver):
    enter_button = driver.find_element(
        By.XPATH,
        '//button[1]',
    )
    enter_button.click()


def push_use_email_button(driver):
    try_email_button = driver.find_element(
        By.XPATH,
        '//div[8]/a',
    )
    try_email_button.click()


def enter_email(driver, ozon_login_email):
    email = ozon_login_email
    email_field = driver.find_element(
        By.XPATH,
        '//div[3]/div/label/div/div/input'
    )
    for _ in email:
        email_field.send_keys(Keys.BACKSPACE)
    email_field.send_keys(email)


def push_get_code_button(driver):
    get_code_button = driver.find_element(
        By.XPATH,
        '//div[4]/button',
    )
    get_code_button.click()


def input_code(driver, google_credentials):
    sleep(15)
    verification_code = get_verification_code(google_credentials)
    print(verification_code)
    code_input_field = driver.find_element(
        By.XPATH,
        '//div[3]/label/div/div/input',
    )
    code_input_field.send_keys(verification_code)


def main():
    clear_temp_folder()
    load_dotenv()
    google_credentials = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    ozon_login_email = os.environ['OZON_LOGIN_EMAIL']
    profile_path = os.environ['FIREFOX_PROFILE_PATH']
    delay_floor = os.environ['ACTION_DELAY_FLOOR']
    delay_ceil = os.environ['ACTION_DELAY_CEIL']
    ozon_url = 'https://seller.ozon.ru'
    with open('run_browser.sh', 'w') as browser_launcher:
        shell_script = f'''#!/bin/bash
        firefox -profile "{profile_path}" --new-tab "{ozon_url}" --headless  &
        sleep 10
        pkill  firefox
        '''
        browser_launcher.write(shell_script)
    while True:
        try:
            driver = prepare_webdriver(profile_path)
            request_actions = [
                partial(pass_to_main_page, ozon_url=ozon_url),
                push_main_page_enter_button,
                push_enter_ozon_id_button,
                push_use_email_button,
                partial(enter_email, ozon_login_email=ozon_login_email),
                push_get_code_button,
                partial(input_code, google_credentials=google_credentials),
            ]
            for action in request_actions:
                action(driver)
                if driver.title == 'Just a moment...':
                    raise CaptchaReceived('Received captcha from Ozon Seller.')
                print(driver.title)
                human_action_delay(delay_floor, delay_ceil)
            sleep(60 * 15)
            human_action_delay(delay_floor, delay_ceil)
        except CaptchaReceived as cr:
            print(cr)
            driver.close()
            subprocess.call("./run_browser.sh", shell=True)
            print('Now bot will be relaunched.')
            human_action_delay(delay_floor, delay_ceil)


if __name__ == '__main__':
    main()
