import json
from ChodeCoin.Backend.objects.admin import Admin, convert_admin_to_json
from ChodeCoin.Backend.helpers.array_helper import ArrayHelper
from ChodeCoin.Backend.helpers.date_helper import DateHelper
from pathlib import Path


class AdminRecordPortal:
    def __init__(self, date_helper=DateHelper(), array_helper=ArrayHelper()):
        self.date_helper = date_helper
        self.array_helper = array_helper
        self.db_path = f"{Path(__file__).parents[1]}/db/admin_users.json"

    def create_new_admin(self, admin_name, admin_permission):
        admin_to_add = Admin(admin_name, admin_permission, self.date_helper.current_timestamp_string())
        new_admin_entry = convert_admin_to_json(admin_to_add)
        with open(self.db_path, "r+") as file:
            record_book = json.load(file)
            record_book["admin_records"].append(new_admin_entry)
        with open(self.db_path, "wt") as file:
            json.dump(record_book, file, indent=4)

    def admin_exists(self, admin_name):
        with open(self.db_path, "r") as file:
            record_book = json.load(file)
            return any(admin_record["name"] == admin_name for admin_record in record_book["admin_records"])

    def get_admin_permission(self, admin_name):
        if self.admin_exists(admin_name):
            with open(self.db_path, "r") as file:
                record_book = json.load(file)
                admin_permission = "4"
                for admin_record in record_book["admin_records"]:
                    if admin_record["name"] == admin_name:
                        admin_permission = admin_record["permission_level"]
            return admin_permission.__str__()
        else:
            return 4

    def set_admin_level(self, target_user, new_admin_level):
        with open(self.db_path, "r+") as file:
            record_book = json.load(file)
            for admin_record in record_book["admin_records"]:
                if admin_record["name"] == target_user:
                    admin_record["permission_level"] = new_admin_level
                    break
        with open(self.db_path, "wt") as file:
            json.dump(record_book, file, indent=4)
