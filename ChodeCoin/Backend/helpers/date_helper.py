import datetime
from ChodeCoin.Backend.helpers.timestamp_helper import TimestampHelper


class DateHelper:
    def __init__(self, timestamp_helper=TimestampHelper()):
        self.timestamp_helper = timestamp_helper

    def is_older_than_six_months(self, date_string: str):
        date_format = "%Y-%m-%d %H:%M:%S"
        current_timestamp_string = self.timestamp_helper.current_timestamp_string()
        current_timestamp = datetime.datetime.strptime(current_timestamp_string, date_format)
        date_object = datetime.datetime.strptime(date_string, date_format)
        cutoff_date = current_timestamp - datetime.timedelta(days=183)

        if date_object <= cutoff_date:
            return True
        else:
            return False
