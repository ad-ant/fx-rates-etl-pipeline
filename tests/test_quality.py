from datetime import date

import pandas as pd
import pytest

from src.quality import MIN_CURRENCIES_PER_DAY, validate_rates


def make_df(rows):
    return pd.DataFrame(rows, columns=["effective_date", "currency_code", "currency_name", "mid_rate"])


def full_day(effective_date):
    return [
        {
            "effective_date": effective_date,
            "currency_code": f"A{chr(65 + i)}{chr(65 + i)}",
            "currency_name": f"currency {i}",
            "mid_rate": 1.0,
        }
        for i in range(MIN_CURRENCIES_PER_DAY)
    ]


def test_validate_rates_accepts_empty_frame():
    validate_rates(make_df([]))


def test_validate_rates_accepts_good_batch():
    validate_rates(make_df(full_day(date(2024, 1, 2))))


def test_validate_rates_rejects_null_in_critical_column():
    rows = full_day(date(2024, 1, 2))
    rows[0]["mid_rate"] = None

    with pytest.raises(ValueError, match="null"):
        validate_rates(make_df(rows))


def test_validate_rates_rejects_negative_mid_rate():
    rows = full_day(date(2024, 1, 2))
    rows[0]["mid_rate"] = -1.0

    with pytest.raises(ValueError, match="negative"):
        validate_rates(make_df(rows))


def test_validate_rates_rejects_bad_currency_code_format():
    rows = full_day(date(2024, 1, 2))
    rows[0]["currency_code"] = "usd"

    with pytest.raises(ValueError, match="currency_code"):
        validate_rates(make_df(rows))


def test_validate_rates_rejects_duplicate_key_in_batch():
    rows = full_day(date(2024, 1, 2))
    rows.append(rows[0])

    with pytest.raises(ValueError, match="duplicate"):
        validate_rates(make_df(rows))


def test_validate_rates_warns_on_low_currency_count():
    rows = full_day(date(2024, 1, 2))[:1]

    with pytest.warns(UserWarning, match="low currency count"):
        validate_rates(make_df(rows))
