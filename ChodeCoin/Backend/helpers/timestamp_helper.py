import datetime


class TimestampHelper:
    def current_timestamp_string(self):
        timestamp = datetime.datetime.now()
        timestamp_string = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return timestamp_string
