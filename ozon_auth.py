import os
import pickle
from functools import partial
from random import randrange
from time import sleep

import geckodriver_autoinstaller
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys

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
    profile.set_preference("dom.webdriver.enabled", False)
    profile.set_preference('useAutomationExtension', False)
    profile.update_preferences()
    desired = DesiredCapabilities.FIREFOX
    driver = webdriver.Firefox(
        firefox_profile=profile,
        desired_capabilities=desired,
    )
    return driver


def pass_to_main_page(driver):
    url = 'https://seller.ozon.ru/'
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
    driver = prepare_webdriver(profile_path)
    try:
        request_actions = [
            pass_to_main_page,
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
        cookies_filepath = f'{ozon_login_email}_cookies'
        with open(cookies_filepath, 'wb') as cookies_file:
            pickle.dump(driver.get_cookies(), cookies_file)
        with open(cookies_filepath, 'rb') as cookies_file:
            for cookie in pickle.load(cookies_file):
                driver.add_cookie(cookie)
        with open(cookies_filepath, 'rb') as cookies_file:
            print(pickle.load(cookies_file))
        driver.refresh()
        human_action_delay(delay_floor, delay_ceil)
        with open(cookies_filepath, 'wb') as cookies_file:
            pickle.dump(driver.get_cookies(), cookies_file)
        with open(cookies_filepath, 'rb') as cookies_file:
            print(pickle.load(cookies_file))

        sleep(1000)
    except CaptchaReceived:
        quit()


if __name__ == '__main__':
    main()
