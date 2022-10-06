import pickle
from random import randrange
from time import sleep

import geckodriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys


class CaptchaReceived(Exception):
    def __init__(self, text):
        self.text = text


def human_delay():
    delay_time = randrange(900, 2500) / 100
    print(delay_time)
    sleep(delay_time)


def request_code_by_email(driver):
    enter_button = driver.find_element(
        By.CLASS_NAME,
        'button-module_content_2JNxj',
    )
    enter_button.click()
    human_delay()
    try_email_button = driver.find_element(
        By.CLASS_NAME,
        'x7ba',
    )
    try_email_button.click()
    human_delay()
    email = 'smalldirtybird@gmail.com'
    email_field = driver.find_element(
        By.NAME,
        'email'
    )
    for _ in email:
        email_field.send_keys(Keys.BACKSPACE)
    email_field.send_keys(email)
    human_delay()
    get_code_button = driver.find_element(
        By.CLASS_NAME,
        'ui-f2',
    )
    get_code_button.click()


def direct_authorization(driver):
    url = 'https://seller.ozon.ru/app/registration/signin'
    driver.get(url)
    human_delay()
    request_code_by_email(driver)


def main_page_authorization(driver):
    url = 'https://seller.ozon.ru/'
    driver.get(url)
    human_delay()
    driver.find_element(
        By.CLASS_NAME,
        'header__button header__button--login button_Tynp0 button--height-small_z-sd+ button--color-black_gwhyR button--font-size-small_tQ5bo button--round_90mcZ button--background-gray_XwSf0'
    )
    human_delay()
    request_code_by_email(driver)


def main():
    '''
    Prepare webdriver.
    '''
    geckodriver_autoinstaller.install()
    profile = webdriver.FirefoxProfile(
        '/home/drew/.mozilla/firefox/mqzcup7s.default-release/')
    profile.set_preference("dom.webdriver.enabled", False)
    profile.set_preference('useAutomationExtension', False)
    profile.update_preferences()
    desired = DesiredCapabilities.FIREFOX
    driver = webdriver.Firefox(
        firefox_profile=profile,
        desired_capabilities=desired,
    )

    '''
    Try to authorize.
    '''
    try:
        direct_authorization(driver)
        if driver.title == 'Just a moment...':
            human_delay()
            main_page_authorization(driver)
        if driver.title == 'Just a moment...':
            raise CaptchaReceived('Recieved captcha from Ozon Seller.')
        pickle.dump(driver.get_cookies(), open('cookies', 'wb'))
        sleep(1000)
    except CaptchaReceived as cr:
        human_delay()
        quit()


if __name__ == '__main__':
    main()
