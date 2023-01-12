import logging
from datetime import datetime
from random import randrange
from time import sleep

from dateutil.relativedelta import relativedelta


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
    if date_range[0] < datetime.now().date():
        date_range[0] += relativedelta(years=+1)
    if date_range[1] < datetime.now().date():
        date_range[1] += relativedelta(years=+1)
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
