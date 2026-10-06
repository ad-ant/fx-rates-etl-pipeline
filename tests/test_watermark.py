from datetime import date

from src.watermark import get_load_window


def test_get_load_window_uses_default_start_when_no_data():
    window = get_load_window(None, date(2024, 1, 10), date(2024, 1, 1))
    assert window == (date(2024, 1, 1), date(2024, 1, 10))


def test_get_load_window_starts_day_after_last_loaded_date():
    window = get_load_window(date(2024, 1, 5), date(2024, 1, 10), date(2024, 1, 1))
    assert window == (date(2024, 1, 6), date(2024, 1, 10))


def test_get_load_window_returns_none_when_up_to_date():
    assert get_load_window(date(2024, 1, 10), date(2024, 1, 10), date(2024, 1, 1)) is None
