from datetime import datetime, timedelta

import gspread


def get_delivery_date_requirements(google_credentials, table_name,
                                   requirements_sheet_name, account_name):
    table = gspread.service_account(google_credentials).open(table_name)
    worksheet = table.worksheet(requirements_sheet_name)
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
                    'current_delivery_date_cell': f'E{row_number}',
                    'processed_cell': f'G{row_number}'
                }
        except ValueError:
            continue
    return delivery_date_requirements


def update_spreadsheet(cell_coordinates, cell_new_value, google_credentials,
                       table_name, requirements_sheet_name,
                       ):
    table = gspread.service_account(google_credentials).open(table_name)
    table.worksheet(requirements_sheet_name).update(
        cell_coordinates,
        str(cell_new_value),
    )


def get_storage_settings(google_credentials, table_name,
                         storage_settings_sheet_name):
    table = gspread.service_account(google_credentials).open(table_name)
    worksheet = table.worksheet(storage_settings_sheet_name)
    storage_settings = {}
    spreadsheet = worksheet.get_all_values()[1:]
    for row in spreadsheet:
        storage_settings.update(
            {
                row[0]: {
                    'upper_timeslot': row[1],
                    'lower_timeslot': row[2],
                }
            }
        )
    return storage_settings
