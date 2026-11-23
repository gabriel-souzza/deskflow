import os
from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def get_office_timezone() -> ZoneInfo:
    tz_name = os.getenv("OFFICE_TIMEZONE", "America/Sao_Paulo")
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, KeyError, ValueError):
        return ZoneInfo("UTC")


def get_office_now() -> datetime:
    """Returns the current wall-clock datetime in the office timezone (naive)."""
    tz = get_office_timezone()
    return datetime.now(tz).replace(tzinfo=None)


def get_office_now_aware() -> datetime:
    """Returns the current wall-clock datetime in the office timezone with UTC tzinfo,
    matching booking.slot.start stored representation.
    """
    return get_office_now().replace(tzinfo=UTC)

