import logging
import os
import subprocess
from datetime import datetime, timedelta
from functools import partial
from random import randrange
from time import sleep

import geckodriver_autoinstaller
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from telegram import Bot

from clear_temp_folder import clear_temp_folder
from spreadsheets_api import (get_delivery_date_requirements,
                              get_storage_settings, update_spreadsheet)
from yandex_mail import get_verification_code

logger = logging.getLogger('TelegramLogger')
STATE = 'START'
web_driver = None
start_time = None


class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def human_action_delay(floor, ceil):
    delay_time = randrange(int(floor) * 1000, int(ceil) * 1000) / 1000
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
    if len(date_range) > 1 and date_range[0] > date_range[1]:
        date_range[1] += relativedelta(years=+1)
    if len(date_range) == 1:
        return tuple(date_range * 2)
    return tuple(date_range)


def rotate_slots_table(slots, columns_quantity, first_column, last_column):
    slots_rotated = []
    column = 1
    row = 0
    for slot in slots:
        slots_rotated.insert(row * column, slot)
        row += 1
        if row == columns_quantity:
            row = 0
            column += 1
    slots_in_column = len(slots_rotated) / columns_quantity
    lower_border = 0
    upper_border = len(slots_rotated)
    if first_column:
        lower_border = int(first_column * slots_in_column)
    if last_column:
        upper_border = int((last_column + 1) * slots_in_column)
    return slots_rotated[lower_border:upper_border]


def limit_hour_rows(slots_table, upper_timeslot, lower_timeslot):
    column_starts = 0
    column_ends = 23
    current_row = column_ends
    limited_slots_table = []
    for slot in slots_table:
        if upper_timeslot <= current_row <= lower_timeslot:
            limited_slots_table.append(slot)
        current_row -= 1
        if current_row == column_starts - 1:
            current_row = column_ends
    return limited_slots_table


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
        firefox_binary='/usr/bin/firefox',
        firefox_profile=profile,
        desired_capabilities=desired,
        options=options,
    )
    return driver


def start(driver, delay, ozon_delivery_page_url, profile_path):
    global web_driver
    global start_time
    logger.info('Бот запущен.')
    start_time = datetime.now()
    clear_temp_folder()
    subprocess.call('./run_browser.sh', shell=True)
    web_driver = prepare_webdriver(profile_path)
    web_driver.get(ozon_delivery_page_url)
    delay()
    if web_driver.title == 'Just a moment...'\
            or web_driver.page_source.find(
            'Произошла ошибка на сервере') != -1:
        return 'BLOCKING_WORKED'
    if web_driver.current_url == ozon_delivery_page_url:
        return 'SWITCH_ACCOUNT'
    else:
        return 'NEED_AUTHENTICATE'


def start_authenticate(driver, delay):
    driver.find_element_by_xpath('//span[contains(text(), "Войти")]').click()
    logger.info('Требуется авторизация.')
    delay()
    if driver.title == 'Just a moment...' \
            or driver.page_source.find('Произошла ошибка на сервере') != -1:
        return 'BLOCKING_WORKED'
    else:
        return 'AUTHENTICATION_PROCESS'


def authenticate_with_email(driver, delay, ozon_login_email, yandex_email,
                            yandex_password, ozon_delivery_page_url):
    logger.info(f'Начало авторизации через почтовый ящик: {ozon_login_email}')
    sleep(5)
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
    if driver.current_url == 'https://seller.ozon.ru/app/registration/signin':
        return 'ACCOUNT_SELECTION'
    else:
        driver.get(ozon_delivery_page_url)
    if driver.title == 'Just a moment...' \
            or driver.page_source.find('Произошла ошибка на сервере') != -1:
        return 'BLOCKING_WORKED'
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
    driver.refresh()
    sleep(10)
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
    left_switcher, current_date_range_string,\
        right_switcher = range_switcher_components
    left_switcher_html = left_switcher.get_attribute('innerHTML')
    right_switcher_html = right_switcher.get_attribute('innerHTML')
    current_date_range = convert_date_range(current_date_range_string.text)
    seen_ranges.append(current_date_range)
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
    available_days = []
    for day in table_header:
        available_days.append(day.text)
    previous_date, last_date = available_date_range
    date_list = []
    for day in available_days:
        date = previous_date.replace(day=int(day))
        if date_list and date < date_list[available_days.index(day) - 1]:
            date = date.replace(month=(date.month + 1))
        date_list.append(date)
    logger.info(f'Доступные даты поставки: {date_list}')
    suitable_dates = []
    for date in date_list:
        if date == desired_date or current_delivery_date < desired_date < date\
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


def choose_delivery_date(driver, delay, google_credentials, table_name,
                         requirements_sheet_name, account_name,
                         storage_sheet_name):
    logger.info(f'Старт обработки таблицы {table_name}.')
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
    for delivery_id, details in delivery_date_requirements.items():
        logger.info(f'Обработка поставки {delivery_id}.')
        if driver.page_source.find(
                'popup-footer-module_footer_QFh20 popup_footer_o5aCa') != -1:
            driver.find_element_by_xpath(
               '//span[contains(text(), "Напомнить позже")]').click()
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
        if driver.title == 'Just a moment...' \
                or driver.page_source.find(
                'Произошла ошибка на сервере') != -1:
            return 'BLOCKING_WORKED'
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
        current_data_button_class = 'orders-table-body-module_dateCell_tKzib'
        table_row = driver.find_element_by_xpath(
            '//tbody')
        table_row_html = table_row.get_attribute('innerHTML')
        storage_name = driver.find_element_by_xpath(
            '//div[contains(@class, '
            '"orders-table-body-module_supplyWarehouseCell_3VyP7")]'
        ).text
        current_delivery_timeslot = driver.find_element_by_xpath(
            '//div[contains(@class, '
            '"orders-table-body-module_cellAdditionalText_3McBH '
            'orders-table-body-module_tdAdditionalText_1IduN")]'
        ).text
        timeslot_start_hour, *_ = current_delivery_timeslot.split(sep=':')
        storage_is_special = bool(storage_name in storage_settings.keys())
        if table_row_html.find(current_data_button_class) == -1:
            current_delivery_date = datetime.now().date() + timedelta(weeks=10)
            current_delivery_date_string = current_delivery_date.strftime(
                '%d.%m.%Y')
            current_delivery_date_button = driver.find_element_by_xpath(
                '//button[contains(text(), "Выбрать")]')
        else:
            current_delivery_date_button = driver.find_element_by_xpath(
                f'//span[contains(@class, "{current_data_button_class}")]')
            current_delivery_date_string = current_delivery_date_button.text
            current_delivery_date = datetime.strptime(
                current_delivery_date_string,
                '%d.%m.%Y',
            ).date()
        desired_date = details['min_date']
        update_details = partial(
            update_spreadsheet,
            google_credentials=google_credentials,
            table_name=table_name,
            requirements_sheet_name=requirements_sheet_name,
        )
        if storage_is_special:
            upper_timeslot = storage_settings[storage_name]['upper_timeslot']
            lower_timeslot = storage_settings[storage_name]['lower_timeslot']
        if current_delivery_date == desired_date and (
                not storage_is_special or storage_is_special and
                upper_timeslot <= timeslot_start_hour <= lower_timeslot):
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
        current_delivery_date_button.click()
        timeslot_sidepage = driver.find_element_by_xpath(
            '//div[contains(@class, '
            '"side-page-content-module_sidePageContent_3QWFS typography-module'
            '_body-500_y4OT3 time-slot-select-dialog_dialog_2bhKD")]')
        cross_button = driver.find_element_by_xpath(
            '//button[contains(@aria-label, "Крестик для закрытия")]')
        if timeslot_sidepage.get_attribute('innerHTML').find(
                'Нет доступных дней и времени') == -1:
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
            logger.info('Нет доступных дней и времени.')
            continue
        delay()
        change_date_range(driver, delay, desired_date, [])
        first_border, last_border = get_slot_search_window(
            driver,
            delay,
            desired_date,
            current_delivery_date,
        )
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
            new_delivery_date_string = driver.find_element_by_xpath(
                '//span[contains(@class, '
                '"orders-table-body-module_dateCell_tKzib")]').text
            new_delivery_date = datetime.strptime(
                new_delivery_date_string,
                '%d.%m.%Y').date()
            search_is_finished = int(new_delivery_date == desired_date)
            update_details(
                details['current_delivery_date_cell'],
                new_delivery_date_string,
                )
            update_details(
                details['processed_cell'],
                search_is_finished,
                )
            logger.info(f'''
                \rДата поставки №{delivery_id} обновлена.
                \rНовая дата поставки: {new_delivery_date_string}.
                ''')
            break
        else:
            if driver.page_source.find('Крестик для закрытия') != -1:
                cross_button.click()
        driver.refresh()
        delay()
    return 'WAIT'


def wait(driver, delay, sleep_time):
    global start_time
    driver.close()
    wakeup_time = start_time + timedelta(minutes=int(sleep_time))
    left_time_to_sleep = wakeup_time - datetime.now()
    logger.info(f'Следующий запуск в {wakeup_time}.')
    if left_time_to_sleep > timedelta(seconds=0):
        sleep(left_time_to_sleep.seconds)
    return 'START'


def handle_blocking(driver, delay):
    logger.info('Получена CAPTCHA, бот будет перезапущен.')
    delay()
    os.system('pkill firefox')
    return 'START'


def handle_statement(profile_path, ozon_delivery_page_url, delay,
                     ozon_login_email, yandex_email, yandex_password,
                     account_name, sleep_time,
                     google_spreadsheet_credentials, table_name,
                     requirements_sheet_name, storage_sheet_name):
    global STATE
    global web_driver
    global start_time
    states = {
        'START': partial(
            start,
            ozon_delivery_page_url=ozon_delivery_page_url,
            profile_path=profile_path,
        ),
        'NEED_AUTHENTICATE': start_authenticate,
        'AUTHENTICATION_PROCESS': partial(
            authenticate_with_email,
            ozon_login_email=ozon_login_email,
            yandex_email=yandex_email,
            yandex_password=yandex_password,
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
            google_credentials=google_spreadsheet_credentials,
            table_name=table_name,
            requirements_sheet_name=requirements_sheet_name,
            account_name=account_name,
            storage_sheet_name=storage_sheet_name,
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
        ozon_url = 'https://seller.ozon.ru/app/supply/' \
                   'orders?filter=SupplyPreparation'
        delay = partial(
                    human_action_delay,
                    floor=delay_floor,
                    ceil=delay_ceil,
                )
        while True:
            handle_statement(
                os.environ['FIREFOX_PROFILE_PATH'],
                ozon_url,
                delay,
                ozon_login_email,
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
