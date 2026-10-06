from datetime import date, timedelta


def get_load_window(
    last_loaded_date: date | None, today: date, default_start: date
) -> tuple[date, date] | None:
    if last_loaded_date is None:
        start = default_start
    else:
        start = last_loaded_date + timedelta(days=1)

    if start > today:
        return None
    return start, today
