import os
from datetime import datetime
from pprint import pprint

import gspread
from dotenv import load_dotenv


def get_delivery_date_requirements(google_credentials, table_name, sheet_name,
                                   account_name):
    table = gspread.service_account(google_credentials).open(table_name)
    worksheet = table.worksheet(sheet_name)
    delivery_date_requirements = {}
    spreadsheet = worksheet.get_all_values()[1:]
    for row in spreadsheet:
        min_date = row[1]
        current_date = row[4]
        if row[5] == account_name:
            delivery_date_requirements[row[0]] = {
                'min_date': datetime.strptime(min_date, '%d.%m.%Y').date(),
                'max_date': datetime.strptime(row[2], '%d.%m.%Y').date(),
                'assembly_time': row[3],
                'current_delivery_date': current_date,
                'current_delivery_date_cell_coordinates':
                    f'E{spreadsheet.index(row) + 2}',
            }
    return delivery_date_requirements


def update_current_delivery_date(google_credentials, table_name, sheet_name,
                                 cell_coordinates, cell_new_value):
    table = gspread.service_account(google_credentials).open(table_name)
    table.worksheet(sheet_name).update(cell_coordinates, cell_new_value)


def main():
    load_dotenv()
    delivery_date_requirements = get_delivery_date_requirements(
        os.environ['GOOGLE_SPREADSHEET_CREDENTIALS'],
        os.environ['TABLE_NAME'],
        os.environ['SHEET_NAME'],
        os.environ['ACCOUNT_NAME'],
    )
    pprint(delivery_date_requirements)
    for delivery_id, details in delivery_date_requirements.items():
        update_current_delivery_date(
            os.environ['GOOGLE_SPREADSHEET_CREDENTIALS'],
            os.environ['TABLE_NAME'],
            os.environ['SHEET_NAME'],
            details['current_delivery_date_cell_coordinates'],
            datetime.now().date().strftime('%d.%m.%Y'),
        )


if __name__ == '__main__':
    main()
