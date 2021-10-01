from datetime import datetime, timezone

from tzlocal import get_localzone


def now(as_local: bool = True) -> datetime:
    """ Get timezone aware current date/time as UTC or local time.

    :param as_local: if True get datetime in local timezone, else in UTC
    :return: datetime
    """
    dt_utc = datetime.utcnow().replace(tzinfo=timezone.utc)

    if not as_local:
        return dt_utc

    return dt_utc.astimezone(get_localzone())
