class Xpath:

    def __init__(self, account_name):
        self.account_name_button = f'//div[contains(text(), "{account_name}")]'
        self.accept_timeslot_button = '//span[contains(@class, "time-slot-select-dialog_submitButton_b2nbQ")]'
        self.chosen_date_time = '//span[contains(@class, "time-slot-select-dialog_selectedTimeslotDateLabel_3QFJq")]'
        self.cross_button = '//button[contains(@aria-label, "Крестик для закрытия")]'
        self.current_account_button = '//span[contains(@class, "index_companyItem_Pae1n index_hasSelect_s1JiM")]'
        self.current_delivery_timeslot = '//div[contains(@class, "orders-table-body-module_cellAdditionalText_3McBH orders-table-body-module_tdAdditionalText_1IduN")]'
        self.date_interval = '//div[contains(@class, "slots-range-switcher_dateSwitcherInterval_220Nq")]'
        self.delivery_search_field = '//input[contains(@placeholder, "Поиск по номеру поставки")]'
        self.delivery_settings_page = '//div[contains(@class, "orders-table-body-module_parentOrderNumber_3mIBW")]'
        self.email_input_field = '//input[contains(@inputmode, "email")]'
        self.enter_button = '//span[contains(text(), "Войти")]'
        self.enter_with_email_button = '//a[contains(text(), "Войти по почте")]'
        self.entries_panel = '//div[contains(@class, "container-fluid")]'
        self.get_verification_code_button = '//span[contains(text(), "Получить код")]'
        self.new_delivery_date_string_raw = '//div[contains(@class, "warehouse-info_timeslot_1HCVC")]'
        self.new_timeslot_start_hour_string = '//div[contains(@class, "warehouse-info_date_357nW")]'
        self.next_button = '//span[contains(text(), "Далее")]'
        self.open_timeslot_side_panel_button = '//div[contains(@class, "warehouse-info_timeslot_1HCVC")]'
        self.range_switcher = '//div[contains(@class, "slots-range-switcher_dateSwitcher_34ExK")]'
        self.remind_later_button = '//span[contains(text(), "Напомнить позже")]'
        self.search_field_button = '//div[contains(text(), "Номер")]'
        self.stay_active_button = '//span[contains(text(), "Оставить активной")]'
        self.timeslot_sidepage = '//div[contains(@class, "side-page-content-module_sidePageContent_3QWFS typography-module_body-500_y4OT3 time-slot-select-dialog_dialog_2bhKD")]'
        self.verification_code_input_field = '//input[contains(@inputmode, "numeric")]'
        self.table_header = '//div[contains(@class, "time-slots-table_slotsTableHead_ERvbR")]'
        self.storage_name = '//div[contains(@class, "orders-table-body-module_supplyWarehouseCell_3VyP7")]'


class ClassName:

    def __init__(self):
        self.datetime_slots = 'time-slots-table_slotsTableContentContainer_1Z9BS'
        self.slots_table = 'time-slots-table_slotsTableCell_MTw9O'
        self.timeslot = 'time-slots-table_cellHeadDate_2VUyD'


class FindInnerHtml:

    def __init__(self):
        self.delivery_search_page_pop_up = 'popup-footer-module_footer_QFh20 popup_footer_o5aCa'
        self.inactive_timeslot = 'time-slots-table_emptyCell_dxX7v'
        self.selected_timeslot = 'time-slots-table_selectedSlot_3H6l9'
