from __future__ import annotations

import datetime
import re
from collections.abc import Callable
from datetime import timedelta
from typing import cast


class Frequencies:
    @staticmethod
    def hourly(t: datetime.datetime) -> datetime.datetime:
        dt = t + datetime.timedelta(hours=1)
        return dt.replace(minute=0, second=0, microsecond=0)

    @staticmethod
    def daily(t: datetime.datetime) -> datetime.datetime:
        dt = t + datetime.timedelta(days=1)
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def weekly(t: datetime.datetime) -> datetime.datetime:
        dt = t + datetime.timedelta(days=7 - t.weekday())
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def monthly(t: datetime.datetime) -> datetime.datetime:
        if t.month == 12:
            y, m = t.year + 1, 1
        else:
            y, m = t.year, t.month + 1
        return t.replace(year=y, month=m, day=1, hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def yearly(t: datetime.datetime) -> datetime.datetime:
        y = t.year + 1
        return t.replace(year=y, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def parse_size(size: str) -> float | None:
    size = size.strip()
    reg = re.compile(r"([e\+\-\.\d]+)\s*([kmgtpezy])?(i)?(b)", flags=re.IGNORECASE)

    match = reg.fullmatch(size)

    if not match:
        return None

    s, u, i, b = match.groups()

    try:
        _s: float = float(s)
    except ValueError as e:
        raise ValueError("Invalid float value while parsing size: '%s'" % s) from e

    _u: int = "kmgtpezy".index(u.lower()) + 1 if u else 0
    _i: int = 1024 if i else 1000
    _b: int = {"b": 8, "B": 1}[b] if b else 1

    # not sure why mypy think this is Any
    return cast(float, _s * _i**_u / _b)


def parse_duration(duration: str) -> None | timedelta:
    duration = duration.strip()
    reg = r"(?:([e\+\-\.\d]+)\s*([a-z]+)[\s\,]*)"

    units = [
        ("y|years?", 31536000),
        ("months?", 2628000),
        ("w|weeks?", 604800),
        ("d|days?", 86400),
        ("h|hours?", 3600),
        ("min(?:ute)?s?", 60),
        ("s|sec(?:ond)?s?", 1),  # spellchecker: disable-line
        ("ms|milliseconds?", 0.001),
        ("us|microseconds?", 0.000001),
    ]

    if not re.fullmatch(reg + "+", duration, flags=re.IGNORECASE):
        return None

    seconds = 0

    for value, unit in re.findall(reg, duration, flags=re.IGNORECASE):
        try:
            value = float(value)
        except ValueError as e:
            raise ValueError("Invalid float value while parsing duration: '%s'" % value) from e

        try:
            unit = next(u for r, u in units if re.fullmatch(r, unit, flags=re.IGNORECASE))
        except StopIteration:
            raise ValueError("Invalid unit value while parsing duration: '%s'" % unit) from None

        seconds += value * unit

    return datetime.timedelta(seconds=seconds)


def parse_frequency(frequency: str) -> None | Callable[[datetime.datetime], datetime.datetime]:
    frequencies = {
        "hourly": Frequencies.hourly,
        "daily": Frequencies.daily,
        "weekly": Frequencies.weekly,
        "monthly": Frequencies.monthly,
        "yearly": Frequencies.yearly,
    }
    frequency = frequency.strip().lower()
    return frequencies.get(frequency)


def parse_day(day: str) -> int | None:
    days = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    day = day.strip().lower()
    if day in days:
        return days[day]
    if day.startswith("w") and day[1:].isdigit():
        _day = int(day[1:])
        if not 0 <= _day < 7:
            raise ValueError(
                "Invalid weekday value while parsing day (expected [0-6]): '%d'" % _day
            )
    else:
        _day = None

    return _day


def parse_time(time: str) -> None | datetime.time:
    time = time.strip()
    reg = re.compile(r"^[\d\.\:]+\s*(?:[ap]m)?$", flags=re.IGNORECASE)

    if not reg.match(time):
        return None

    formats = [
        "%H",
        "%H:%M",
        "%H:%M:%S",
        "%H:%M:%S.%f",
        "%I %p",
        "%I:%M %S",
        "%I:%M:%S %p",
        "%I:%M:%S.%f %p",
    ]

    for format_ in formats:
        try:
            dt = datetime.datetime.strptime(time, format_)
        except ValueError:
            pass
        else:
            return dt.time()

    raise ValueError("Unrecognized format while parsing time: '%s'" % time)


def parse_daytime(daytime: str) -> None | tuple[int | None, datetime.time | None]:
    daytime = daytime.strip()
    reg = re.compile(r"^(.*?)\s+at\s+(.*)$", flags=re.IGNORECASE)

    match = reg.match(daytime)
    if match:
        day, time = match.groups()
    else:
        day = time = daytime

    try:
        day = parse_day(day)
        if match and day is None:
            raise ValueError
    except ValueError as e:
        raise ValueError("Invalid day while parsing daytime: '%s'" % day) from e

    try:
        time = parse_time(time)
        if match and time is None:
            raise ValueError
    except ValueError as e:
        raise ValueError("Invalid time while parsing daytime: '%s'" % time) from e

    if day is None and time is None:
        return None

    return day, time
