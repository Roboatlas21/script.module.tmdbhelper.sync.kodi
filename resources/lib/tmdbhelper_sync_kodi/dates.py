import datetime
from tmdbhelper.lib.addon.tmdate import convert_timestamp, get_timestring_zulu, get_datetime_now


def kodi_date_to_zulu(value):
    if not value:
        return
    local_date = convert_timestamp(value, time_fmt='%Y-%m-%d %H:%M:%S')
    return get_timestring_zulu(local_date.astimezone(datetime.timezone.utc))


def get_kodi_date_now():
    return get_datetime_now().strftime('%Y-%m-%d %H:%M:%S')
