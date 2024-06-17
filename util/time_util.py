import datetime
import time
from datetime import datetime as dtime

import pytz


# return current timestamp in nanoeconds
def timeNow():
    return int(time.time() * 1000 * 1000)


def callTimeNow(iso2Code):
    servertimezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    timestamp = timeNow()
    serverDatetime = dtime.fromtimestamp(timestamp / 1e6).astimezone(servertimezone)
    timezones = pytz.country_timezones.get(iso2Code, [])
    zone = timezones[0]
    targetTimezone = pytz.timezone(zone)
    targetDatetime = serverDatetime.astimezone(targetTimezone)
    targetTimestamp = int(targetDatetime.timestamp() * 1e6)
    return targetTimestamp


def offset(iso2Code):
    servertimezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    try:
        targetTimezones = pytz.country_timezones.get(iso2Code, [])
        if targetTimezones:
            targetTimezone = pytz.timezone(targetTimezones[0])
            serverTime = dtime.now(servertimezone)
            targetTime = serverTime.astimezone(targetTimezone)
            offsetSeconds = int((targetTime.utcoffset() - serverTime.utcoffset()).total_seconds())
            print(f"Offset from {servertimezone} to {targetTimezones[0]}: {offsetSeconds} seconds")
            return offsetSeconds
        else:
            print(f"No timezones found for ISO 2-code: {iso2Code}")
            return None
    except pytz.exceptions.UnknownTimeZoneError:
        print(f"Unknown timezone for ISO 2-code: {iso2Code}")
        return None


def tStampToLocalTStamp(tStamp, isoCode):
    targetTimezones = pytz.country_timezones.get(isoCode, [])
    if targetTimezones:
        targetTimezone = pytz.timezone(targetTimezones[0])
        locTime = int(pytz.utc.localize(tStamp).astimezone(targetTimezone).timestamp())
        print(f"TimeStamp to {targetTimezones[0]} TimeStamp : {locTime} seconds")
        return locTime
    else:
        print(f"No timezones found for ISO 2-code: {isoCode}")
        return None


class TimeUtil:

    @staticmethod
    def getSystemTimeInMilliseconds():
        dt = dtime.now()
        hh = int(dt.strftime('%H')) * 60 * 60
        mm = int(dt.strftime('%M')) * 60
        ss = int(dt.strftime('%S'))
        ms = int(dt.strftime('%f')[:-3])
        return int(hh + mm + ss) * 1000 + ms

    @staticmethod
    def getDayOfThisWeek():
        return int(dtime.now().strftime('%w'))

    @staticmethod
    def getDayOfThisWeekFromTimestamp(tmp):
        return int(dtime.fromtimestamp(tmp).strftime('%w'))


