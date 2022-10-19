import os
from datetime import datetime, timedelta
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
        delivery_id = row[0]
        current_delivery_date = None
        try:
            if row[4]:
                current_delivery_date = datetime.strptime(
                    row[4],
                    '%d.%m.%Y',
                ).date()
            min_date = datetime.strptime(row[1], '%d.%m.%Y').date()
            assembly_time = timedelta(days=int(row[3]))
            today = datetime.now().date()
            if min_date - today < assembly_time:
                min_date = today + assembly_time
            row_number = spreadsheet.index(row) + 2
            if row[5] == account_name and row[6] != '1':
                delivery_date_requirements[delivery_id] = {
                    'min_date': min_date,
                    'max_date': datetime.strptime(row[2], '%d.%m.%Y').date(),
                    'assembly_time': assembly_time,
                    'current_delivery_date': current_delivery_date,
                    'current_delivery_date_cell_coordinates': f'E{row_number}',
                    'processed_cell': f'G{row_number}'
                }
        except ValueError:
            continue
    return delivery_date_requirements


def update_spreadsheet(google_credentials, table_name, sheet_name,
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
        update_spreadsheet(
            os.environ['GOOGLE_SPREADSHEET_CREDENTIALS'],
            os.environ['TABLE_NAME'],
            os.environ['SHEET_NAME'],
            details['current_delivery_date_cell_coordinates'],
            datetime.now().date().strftime('%d.%m.%Y'),
        )


if __name__ == '__main__':
    main()
