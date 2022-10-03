import os
from pprint import pprint

import gspread
from dotenv import load_dotenv


def get_delivery_date_requirements(service_account, table_name, sheet_name,
                                   account_number):
    table = service_account.open(table_name)
    worksheet = table.worksheet(sheet_name)
    delivery_date_requirements = {}
    for row in worksheet.get_all_values()[1:]:
        if row[5] == account_number:
            delivery_date_requirements[row[0]] = {
                'min_date': row[1],
                'max_date': row[2],
                'assembly_time': row[3],
                'current_delivery_date': row[4],
            }
    return delivery_date_requirements


def main():
    load_dotenv()
    service_account = gspread.service_account(
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'],
    )
    delivery_date_requirements = get_delivery_date_requirements(
        service_account,
        os.environ['TABLE_NAME'],
        os.environ['SHEET_NAME'],
        os.environ['ACCOUNT_NUMBER'],
    )
    pprint(delivery_date_requirements)


if __name__ == '__main__':
    main()
