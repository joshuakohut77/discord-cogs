import datetime


class DateHelper:
    def current_timestamp_string(self):
        timestamp = datetime.datetime.now()
        timestamp_string = str(timestamp)
        return timestamp_string
