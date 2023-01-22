import datetime


class TimestampHelper:
    def current_timestamp_string(self):
        timestamp = datetime.datetime.now()
        timestamp_string = timestamp.strftime("%Y-%m-% , %H:%M:%S")
        return timestamp_string
