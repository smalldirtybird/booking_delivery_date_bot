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
    for row in worksheet.get_all_values()[1:]:
        if row[5] == account_name:
            delivery_date_requirements[row[0]] = {
                'min_date': datetime.strptime(row[1], '%d.%m.%Y').date(),
                'max_date': datetime.strptime(row[2], '%d.%m.%Y').date(),
                'assembly_time': row[3],
                'current_delivery_date': row[4],
            }
    return delivery_date_requirements


def main():
    load_dotenv()
    delivery_date_requirements = get_delivery_date_requirements(
        os.environ['GOOGLE_SPREADSHEET_CREDENTIALS'],
        os.environ['TABLE_NAME'],
        os.environ['SHEET_NAME'],
        os.environ['ACCOUNT_NAME'],
    )
    pprint(delivery_date_requirements)


if __name__ == '__main__':
    main()
