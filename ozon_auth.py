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


def human_delay():
    delay_time = randrange(500, 1500) / 100
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


def push_enter_button(driver):
    enter_button = driver.find_element(
        By.XPATH,
        '//button[1]',
    )
    enter_button.click()
    if driver.title == 'Just a moment...':
        raise CaptchaReceived('Received captcha from Ozon Seller.')
    print(driver.title)
    human_delay()


def push_use_email_button(driver):
    try_email_button = driver.find_element(
        By.XPATH,
        '//div[8]/a',
    )
    try_email_button.click()
    if driver.title == 'Just a moment...':
        raise CaptchaReceived('Received captcha from Ozon Seller.')
    print(driver.title)
    human_delay()


def enter_email(driver, ozon_login_email):
    email = ozon_login_email
    email_field = driver.find_element(
        By.XPATH,
        '//div[3]/div/label/div/div/input'
    )
    for _ in email:
        email_field.send_keys(Keys.BACKSPACE)
    email_field.send_keys(email)
    if driver.title == 'Just a moment...':
        raise CaptchaReceived('Received captcha from Ozon Seller.')
    print(driver.title)
    human_delay()


def push_get_code_button(driver):
    get_code_button = driver.find_element(
        By.XPATH,
        '//div[4]/button',
    )
    get_code_button.click()
    if driver.title == 'Just a moment...':
        raise CaptchaReceived('Received captcha from Ozon Seller.')
    print(driver.title)
    human_delay()


def input_code(driver, google_credentials):
    sleep(15)
    verification_code = get_verification_code(google_credentials)
    print(verification_code)
    code_input_field = driver.find_element(
        By.XPATH,
        '//div[3]/label/div/div/input',
    )
    code_input_field.send_keys(verification_code)
    if driver.title == 'Just a moment...':
        raise CaptchaReceived('Received captcha from Ozon Seller.')
    print(driver.title)
    human_delay()


def request_code_by_email(driver, google_credentials, ozon_login_email):
    push_enter_button(driver)
    push_use_email_button(driver)
    enter_email(driver, ozon_login_email)
    push_get_code_button(driver)
    input_code(driver, google_credentials)


def login_page_authorization(driver, google_credentials, ozon_login_email):
    url = 'https://seller.ozon.ru/app/registration/signin'
    driver.get(url)
    if driver.title == 'Just a moment...':
        raise CaptchaReceived('Received captcha from Ozon Seller.')
    print(driver.title)
    human_delay()
    request_code_by_email(driver, google_credentials, ozon_login_email)


def main_page_authorization(driver, google_credentials, ozon_login_email):
    url = 'https://seller.ozon.ru/'
    driver.get(url)
    if driver.title == 'Just a moment...':
        raise CaptchaReceived('Received captcha from Ozon Seller.')
    print(driver.title)
    human_delay()
    enter_button = driver.find_element(
        By.XPATH,
        '//div[3]/a',
    )
    enter_button.click()
    if driver.title == 'Just a moment...':
        raise CaptchaReceived('Received captcha from Ozon Seller.')
    print(driver.title)
    human_delay()
    request_code_by_email(driver, google_credentials, ozon_login_email)


def main():
    clear_temp_folder()
    load_dotenv()
    google_credentials = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    ozon_login_email = os.environ['OZON_LOGIN_EMAIL']

    profile_path = '/home/drew/.mozilla/firefox/mqzcup7s.default-release/'
    driver = prepare_webdriver(profile_path)
    try:
        login_page_authorization(driver, google_credentials, ozon_login_email)
        # main_page_authorization(driver, google_credentials, ozon_login_email)
        if driver.title == 'Just a moment...':
            raise CaptchaReceived('Received captcha from Ozon Seller.')
        sleep(1000)
    except CaptchaReceived:
        quit()


if __name__ == '__main__':
    main()
