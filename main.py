import logging
import os
import platform
import shutil
import subprocess
from datetime import datetime, timedelta
from functools import partial
from time import sleep

import geckodriver_autoinstaller
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from telegram import Bot

from bot_functions import (TelegramLogsHandler, convert_date_range,
                           human_action_delay, limit_hour_rows,
                           rotate_slots_table)
from spreadsheets_api import (get_delivery_date_requirements,
                              get_storage_settings, update_spreadsheet)
from yandex_mail import get_verification_code

logger = logging.getLogger('TelegramLogger')
STATE = 'START'
web_driver = None
start_time = None


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


def handle_blocking(driver, delay):
    logger.info('Получена CAPTCHA, бот будет перезапущен.')
    delay()
    driver.close()
    return 'START'


def start(driver, delay, ozon_delivery_page_url):
    global start_time
    logger.info('Бот запущен.')
    start_time = datetime.now()
    pathname_templates = ['rust_mozprofile', 'tmp']
    if platform.system() == 'Linux':
        tempfolder = '/tmp'
    else:
        return
    tempfolder_content = os.listdir(tempfolder)
    for element in tempfolder_content:
        element_path = os.path.join(tempfolder, element)
        for template in pathname_templates:
            if os.path.isdir(element_path) and template in element \
                    and 'snap-private-tmp' not in element \
                    and 'systemd-private' not in element:
                shutil.rmtree(element_path)
    driver.get(ozon_delivery_page_url)
    delay()
    if driver.title == 'Just a moment...'\
            or driver.page_source.find(
            'Произошла ошибка на сервере') != -1:
        return 'BLOCKING_WORKED'
    if driver.current_url == ozon_delivery_page_url:
        return 'SWITCH_ACCOUNT'
    else:
        return 'NEED_AUTHENTICATE'


def start_authenticate(driver, delay):
    driver.find_element_by_xpath('//span[contains(text(), "Войти")]').click()
    logger.info('Требуется авторизация.')
    if driver.page_source.find('Войти по почте') == -1:
        driver.refresh()
    delay()
    if driver.title == 'Just a moment...' \
            or driver.page_source.find('Произошла ошибка на сервере') != -1:
        return 'BLOCKING_WORKED'
    else:
        return 'AUTHENTICATION_PROCESS'


def authenticate_with_email(driver, delay, ozon_login_email, yandex_email,
                            yandex_password, ozon_delivery_page_url,
                            signin_url):
    logger.info(f'Начало авторизации через почтовый ящик: {ozon_login_email}')
    sleep(1000)
    driver.find_element_by_xpath(
        '//a[contains(text(), "Войти по почте")]').click()
    delay()
    email_field = driver.find_element_by_xpath(
        '//input[contains(@inputmode, "email")]')
    for _ in ozon_login_email:
        email_field.send_keys(Keys.BACKSPACE)
    email_field.send_keys(ozon_login_email)
    delay()
    driver.find_element_by_xpath(
        '//span[contains(text(), "Получить код")]').click()
    sleep(15)
    delay()
    verification_code = get_verification_code(yandex_email, yandex_password)
    driver.find_element_by_xpath(
        '//input[contains(@inputmode, "numeric")]').send_keys(
        verification_code)
    delay()
    if driver.title == 'Just a moment...' \
            or driver.page_source.find('Произошла ошибка на сервере') != -1:
        return 'BLOCKING_WORKED'
    if driver.current_url == signin_url:
        return 'ACCOUNT_SELECTION'
    if driver.current_url == ozon_delivery_page_url:
        return 'SWITCH_ACCOUNT'


def select_account(driver, delay, account_name, ozon_delivery_page_url):
    logger.info(f'Переключение на аккаунт {account_name}')
    driver.find_element_by_xpath(
        f'//div[contains(text(), "{account_name}")]').click()
    delay()
    driver.find_element_by_xpath('//span[contains(text(), "Далее")]').click()
    delay()
    if driver.title == 'Just a moment...' \
            or driver.page_source.find('Произошла ошибка на сервере') != -1:
        return 'BLOCKING_WORKED'
    if driver.current_url == 'https://seller.ozon.ru/app/dashboard/main':
        driver.get(ozon_delivery_page_url)
    if driver.current_url == ozon_delivery_page_url:
        return 'DELIVERY_MANAGEMENT'


def switch_account(driver, delay, account_name, ozon_delivery_page_url):
    logger.info(f'Переключение на аккаунт {account_name}')
    delay()
    current_account_button = driver.find_element_by_xpath(
        '//span[contains(@class, '
        '"index_companyItem_Pae1n index_hasSelect_s1JiM")]')
    if current_account_button.text == account_name:
        return'DELIVERY_MANAGEMENT'
    current_account_button.click()
    delay()
    driver.find_element_by_xpath(
        f'//div[contains(text(), "{account_name}")]').click()
    delay()
    if driver.title == 'Just a moment...' \
            or driver.page_source.find(
            'Произошла ошибка на сервере') != -1:
        return 'BLOCKING_WORKED'
    if driver.current_url == ozon_delivery_page_url:
        return 'DELIVERY_MANAGEMENT'


def change_date_range(driver, delay, desired_date, seen_ranges):
    range_switcher = driver.find_element_by_xpath(
        '//div[contains(@class, "slots-range-switcher_dateSwitcher_34ExK")]')
    range_switcher_components = range_switcher.find_elements_by_tag_name('div')
    if len(range_switcher_components) == 1:
        return
    left_switcher, current_date_range_string, \
        right_switcher = range_switcher_components
    left_switcher_html = left_switcher.get_attribute('innerHTML')
    right_switcher_html = right_switcher.get_attribute('innerHTML')
    current_date_range = convert_date_range(current_date_range_string.text)
    seen_ranges.append(current_date_range)
    if min(current_date_range) >= desired_date <= max(current_date_range):
        return
    if desired_date < min(current_date_range) \
            and left_switcher_html.find('disabled="disabled"') == -1:
        left_switcher.click()
        delay()
    if desired_date > max(current_date_range) \
            and right_switcher_html.find('disabled="disabled"') == -1:
        right_switcher.click()
        delay()
    if convert_date_range(driver.find_element_by_xpath(
            '//div[contains(@class, '
            '"slots-range-switcher_dateSwitcherInterval_220Nq")]').text) \
            not in seen_ranges:
        change_date_range(driver, delay, desired_date, seen_ranges)
    else:
        return


def get_slot_search_window(driver, delay, desired_date, current_delivery_date):
    available_date_range = convert_date_range(
        driver.find_element_by_xpath(
            '//div[contains(@class, '
            '"slots-range-switcher_dateSwitcherInterval_220Nq")]').text
    )
    table_header = driver.find_element_by_xpath(
        '//div[contains(@class, '
        '"time-slots-table_slotsTableHead_ERvbR")]'
    ).find_elements_by_class_name(
        'time-slots-table_cellHeadDate_2VUyD')
    available_days = [day.text for day in table_header]
    previous_date, last_date = available_date_range
    date_list = []
    for day in available_days:
        date = previous_date.replace(day=int(day))
        if date_list and date < date_list[available_days.index(day) - 1]:
            month = date.month if date.month < 12 else date.month - 12
            date = date.replace(month=(month + 1))
        date_list.append(date)
    logger.info(f'Доступные даты поставки: {date_list}')
    suitable_dates = []
    for date in date_list:
        if date == desired_date \
                or current_delivery_date < desired_date < date \
                or current_delivery_date > desired_date and \
                desired_date < date < current_delivery_date:
            suitable_dates.append(date)
    first_available_date_index = None
    last_available_date_index = None
    if suitable_dates:
        first_available_date_index = date_list.index(min(suitable_dates))
        last_available_date_index = date_list.index(max(suitable_dates))
    logger.info(f'Из них подходящих под критерии поиска: {suitable_dates}')
    return first_available_date_index, last_available_date_index


def wait(driver, delay, sleep_time):
    global start_time
    driver.close()
    wakeup_time = start_time + timedelta(minutes=int(sleep_time))
    left_time_to_sleep = wakeup_time - datetime.now()
    logger.info(f'Следующий запуск в {wakeup_time}.')
    if left_time_to_sleep > timedelta(seconds=0):
        sleep(left_time_to_sleep.seconds)
    return 'START'


def choose_delivery_date(driver, delay, google_credentials, table_name,
                         requirements_sheet_name, account_name,
                         storage_sheet_name, start_page):
    if driver.page_source.find(
            'Произошла ошибка на сервере') != -1:
        driver.refresh()

    # Загрузка данных для поиска поставок из таблицы
    delivery_date_requirements = get_delivery_date_requirements(
        google_credentials,
        table_name,
        requirements_sheet_name,
        account_name,
    ),
    storage_settings = get_storage_settings(
        google_credentials,
        table_name,
        storage_sheet_name,
    )
    if type(delivery_date_requirements) is tuple:
        delivery_date_requirements = delivery_date_requirements[0]

    # Проверка наличия и закрытие объявления
    if driver.page_source.find(
            'popup-footer-module_footer_QFh20 popup_footer_o5aCa') != -1:
        driver.find_element_by_xpath(
            '//span[contains(text(), "Напомнить позже")]').click()
    logger.info(f'Старт обработки таблицы {table_name}.')

    # Обработка поставок в цикле
    for delivery_id, details in delivery_date_requirements.items():
        driver.get(start_page)
        delay()
        if driver.title == 'Just a moment...' or driver.page_source.find(
                'Произошла ошибка на сервере') != -1:
            return 'BLOCKING_WORKED'
        logger.info(f'Обработка поставки {delivery_id}.')

        # Поиск поставки в списке
        search_field_button = WebDriverWait(driver, 20).until(
            expected_conditions.element_to_be_clickable((
                By.XPATH,
                '//div[contains(text(), "Номер")]',
            )))
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
        if driver.find_element_by_xpath(
            '//div[contains(@class, "container-fluid")]').get_attribute(
            'innerHTML').find(
                    'Нет записей') != -1:
            logger.info(f'''
                \rПоставка № {delivery_id} не найдена в списках {account_name}.
                \rПроверьте корректность информации в таблице {table_name}.
                ''')
            driver.refresh()
            delay()
            continue
        logger.info(f'Поставка {delivery_id} найдена.')

        # Определение режима поставок на склад
        storage_name = driver.find_element_by_xpath(
            '//div[contains(@class, '
            '"orders-table-body-module_supplyWarehouseCell_3VyP7")]'
        ).text
        storage_is_special = bool(storage_name in storage_settings.keys())

        # Определение текущего таймслота поставки
        current_delivery_timeslot = driver.find_element_by_xpath(
            '//div[contains(@class, '
            '"orders-table-body-module_cellAdditionalText_3McBH '
            'orders-table-body-module_tdAdditionalText_1IduN")]'
        )
        current_delivery_date_string = \
            current_delivery_timeslot.find_element_by_xpath('..').text[0:10]
        current_delivery_date = datetime.strptime(
            current_delivery_date_string,
            '%d.%m.%Y',
        ).date()
        timeslot_start_hour, *_ = current_delivery_timeslot.text.split(sep=':')

        # Подготовка коллбэка на обновление таблицы
        update_details = partial(
            update_spreadsheet,
            google_credentials=google_credentials,
            table_name=table_name,
            requirements_sheet_name=requirements_sheet_name,
        )

        # Извлечение условий поставки из таблицы
        if storage_is_special:
            upper_timeslot = storage_settings[storage_name]['upper_timeslot']
            lower_timeslot = storage_settings[storage_name]['lower_timeslot']
        else:
            upper_timeslot = 0
            lower_timeslot = 23
        desired_date = details['min_date']

        # Переход дальше по циклу, если таймслот уже установлен
        if current_delivery_date == desired_date and int(upper_timeslot) <= \
                int(timeslot_start_hour) <= int(lower_timeslot):
            search_is_finished = 1
            update_details(
                details['current_delivery_date_cell'],
                current_delivery_date_string,
                )
            update_details(
                details['processed_cell'],
                search_is_finished,
                )
            logger.info(f'''
                \rЖелаемая дата поставки №{delivery_id} уже установлена:
                \r{current_delivery_date}.
                ''')
            continue

        # Переход на страницу выбора таймслота, если таймслот не подходит
        driver.find_element_by_xpath(
            '//div[contains(@class, '
            '"orders-table-body-module_parentOrderNumber_3mIBW")]').click()
        if driver.title == 'Just a moment...' or driver.page_source.find(
                'Произошла ошибка на сервере') != -1:
            return 'BLOCKING_WORKED'
        delay()

        # Обработка всплывающего окна
        if driver.page_source.find('Заявка попадёт в архив') != -1:
            driver.find_element_by_xpath(
                '//span[contains(text(), "Оставить активной")]').click()

        # Открытие сайд-панели с таймслотами
        driver.find_element_by_xpath(
                '//div[contains(@class, "warehouse-info_timeslot_1HCVC")]'
        ).click()
        timeslot_sidepage = driver.find_element_by_xpath(
            '//div[contains(@class, '
            '"side-page-content-module_sidePageContent_3QWFS typography-module'
            '_body-500_y4OT3 time-slot-select-dialog_dialog_2bhKD")]')
        cross_button = driver.find_element_by_xpath(
            '//button[contains(@aria-label, "Крестик для закрытия")]')
        if driver.page_source.find(
                'Произошла ошибка') != -1:
            driver.refresh()

        # Закрытие панели, если нет доступных таймслотов, обновление таблицы,
        # переход дальше по циклу
        if timeslot_sidepage.get_attribute('innerHTML').find(
                'Нет доступных дней и времени') != -1:
            cross_button.click()
            search_is_finished = 0
            update_details(
                details['current_delivery_date_cell'],
                current_delivery_date_string,
            )
            update_details(
                details['processed_cell'],
                search_is_finished,
            )
            logger.info('Нет доступных дней и времени или произошла ошибка.')
            continue
        delay()

        # Выбор диапазона дат, подходящего под условия из таблицы
        change_date_range(driver, delay, desired_date, [])

        # Поиск столбцов, подходящих для выбора таймслота
        first_border, last_border = get_slot_search_window(
            driver,
            delay,
            desired_date,
            current_delivery_date,
        )

        # Переход дальше по циклу, если не найдено подходящих дат для поставки,
        # обновление таблицы.
        if first_border is None:
            cross_button.click()
            search_is_finished = 0
            update_details(
                details['current_delivery_date_cell'],
                current_delivery_date_string,
                )
            update_details(
                details['processed_cell'],
                search_is_finished,
                )
            logger.info('Не обнаружено подходящих слотов.')
            continue

        datetime_slots = driver.find_element_by_class_name(
            'time-slots-table_slotsTableContentContainer_1Z9BS')
        slots_table = rotate_slots_table(
            datetime_slots.find_elements_by_class_name(
                'time-slots-table_slotsTableCell_MTw9O'),
            7,
            first_border,
            last_border,
        )
        if storage_is_special:
            slots_table = limit_hour_rows(
                slots_table,
                int(upper_timeslot),
                int(lower_timeslot),
            )
        for slot in slots_table:
            if slot.get_attribute('innerHTML').find(
                    'time-slots-table_emptyCell_dxX7v') != -1:
                continue
            else:
                slot.click()
            if slot.get_attribute('innerHTML').find(
                    'time-slots-table_selectedSlot_3H6l9') == -1:
                continue
            chosen_date_time = driver.find_element_by_xpath(
                '//span[contains(@class, "time-slot-select-dialog_'
                'selectedTimeslotDateLabel_3QFJq")]'
            ).find_element_by_xpath('../.').text
            chosen_date, chosen_time = chosen_date_time.split(
                sep='Время: ')
            _, cleared_date = chosen_date.split(sep=', ')
            formatted_chosen_date, _ = convert_date_range(
                f'{cleared_date} — {cleared_date}')
            if desired_date < current_delivery_date < \
                    formatted_chosen_date:
                slot.click()
                delay()
                cross_button.click()
                search_is_finished = 0
                update_details(
                    details['current_delivery_date_cell'],
                    current_delivery_date_string,
                    )
                update_details(
                    details['processed_cell'],
                    search_is_finished,
                    )
                logger.info('Не обнаружено подходящих слотов.')
                break
            elif formatted_chosen_date < desired_date:
                slot.click()
                delay()
                continue
            elif driver.find_element_by_xpath(
                    '//span[contains(@class, "time-slot-select-dialog_submitB'
                    'utton_b2nbQ")]').get_attribute('innerHTML').find(
                    'disabled="disabled"') != -1:
                cross_button.click()
                search_is_finished = 0
                update_details(
                    details['current_delivery_date_cell'],
                    current_delivery_date_string,
                )
                update_details(
                    details['processed_cell'],
                    search_is_finished,
                )
                logger.info('Не обнаружено подходящих слотов.')
                break
            else:
                driver.find_element_by_class_name(
                    'custom-button_text_2H7oV').click()
            delay()
            new_delivery_date_string_raw = driver.find_element_by_xpath(
                '//div[contains(@class, "warehouse-info_timeslot_1HCVC")]')
            new_delivery_date_string = ' — '.join((
                new_delivery_date_string_raw.text,
                new_delivery_date_string_raw.text
            ))
            new_delivery_date = convert_date_range(new_delivery_date_string)[0]
            new_timeslot_start_hour_string = driver.find_element_by_xpath(
                '//div[contains(@class, "warehouse-info_date_357nW")]').text
            new_timeslot_start = new_timeslot_start_hour_string.replace(
                new_delivery_date_string_raw.text + '\n', '')[:2]

            search_is_finished = (int(
                new_delivery_date == desired_date
                and int(upper_timeslot) <= int(
                    new_timeslot_start) <= int(lower_timeslot)))

            update_details(
                details['current_delivery_date_cell'],
                new_delivery_date.strftime('%d.%m.%Y'),
                )
            update_details(
                details['processed_cell'],
                search_is_finished,
                )
            logger.info(f'''
                \rДата поставки №{delivery_id} обновлена.
                \rНовая дата поставки:
                {new_delivery_date.strftime('%d.%m.%Y')}.
                ''')
            break
        else:
            if driver.page_source.find('Крестик для закрытия') != -1:
                cross_button.click()
        driver.refresh()
        delay()
    return 'WAIT'


def handle_statement(profile_path, ozon_delivery_page_url, delay,
                     ozon_login_email, signin_url, yandex_email,
                     yandex_password, account_name, sleep_time,
                     google_spreadsheet_credentials, table_name,
                     requirements_sheet_name, storage_sheet_name):
    global STATE
    global web_driver
    global start_time
    states = {
        'START': partial(start, ozon_delivery_page_url=ozon_delivery_page_url),
        'NEED_AUTHENTICATE': start_authenticate,
        'AUTHENTICATION_PROCESS': partial(
            authenticate_with_email,
            ozon_login_email=ozon_login_email,
            yandex_email=yandex_email,
            yandex_password=yandex_password,
            ozon_delivery_page_url=ozon_delivery_page_url,
            signin_url=signin_url,
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
            google_credentials=google_spreadsheet_credentials,
            table_name=table_name,
            requirements_sheet_name=requirements_sheet_name,
            account_name=account_name,
            storage_sheet_name=storage_sheet_name,
            start_page=ozon_delivery_page_url,
        ),
        'WAIT': partial(wait, sleep_time=sleep_time),
        'BLOCKING_WORKED': handle_blocking,
    }
    STATE = states[STATE](web_driver, delay)


def main():
    try:
        load_dotenv()
        tg_bot = Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
        tg_chat_id = os.environ['TELEGRAM_CHAT_ID']
        logger.addHandler(TelegramLogsHandler(tg_bot, tg_chat_id))
        logger.setLevel(logging.INFO)
        ozon_login_email = os.environ['OZON_LOGIN_EMAIL']
        delay_floor = os.environ['ACTION_DELAY_FLOOR']
        delay_ceil = os.environ['ACTION_DELAY_CEIL']
        ozon_url = os.environ['START_URL']
        browser_profile_path = os.environ['FIREFOX_PROFILE_PATH']
        delay = partial(
                    human_action_delay,
                    floor=delay_floor,
                    ceil=delay_ceil,
                )
        clean_browser_profile = os.environ['CLEAN_BROWSER_PROFILE_PATH']
        subprocess.run(
            f'pkill firefox; rm -rf {browser_profile_path}*;'
            f'cp -r {clean_browser_profile}* {browser_profile_path}',
            shell=True,
            stdout=subprocess.PIPE,
        )
        subprocess.run(
            f'./run_browser.sh "{ozon_url}" {browser_profile_path}',
            shell=True,
            stdout=subprocess.PIPE,
        )
        global web_driver
        web_driver = prepare_webdriver(browser_profile_path)
        while True:
            handle_statement(
                browser_profile_path,
                ozon_url,
                delay,
                ozon_login_email,
                os.environ['SIGNIN_URL'],
                os.environ['YANDEX_EMAIL'],
                os.environ['YANDEX_PASSWORD'],
                os.environ['ACCOUNT_NAME'],
                os.environ['SLEEP_TIME_MINUTES'],
                os.environ['GOOGLE_SPREADSHEET_CREDENTIALS'],
                os.environ['TABLE_NAME'],
                os.environ['REQUIREMENTS_SHEET_NAME'],
                os.environ['STORAGE_SETTINGS_SHEET_NAME'],
            )
    except Exception:
        logger.exception(
            'Бот упал и будет перезапущен. Ошибка:')
        os.system('pkill firefox')
        os.system(f'python3 {__file__}')


if __name__ == '__main__':
    main()
