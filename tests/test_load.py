from datetime import date

import pandas as pd
import pytest

from src.db import get_connection
from src.load import upsert_rates


@pytest.fixture
def conn():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("truncate table exchange_rates")
    conn.commit()
    yield conn
    conn.close()


def make_df(rows):
    return pd.DataFrame(rows, columns=["effective_date", "currency_code", "currency_name", "mid_rate"])


def test_upsert_rates_reload_same_batch_does_not_duplicate(conn):
    df = make_df([
        {"effective_date": date(2024, 1, 2), "currency_code": "USD", "currency_name": "dolar amerykanski", "mid_rate": 4.0},
    ])

    upsert_rates(conn, df)
    upsert_rates(conn, df)

    with conn.cursor() as cur:
        cur.execute("select count(*) from exchange_rates")
        (count,) = cur.fetchone()
    assert count == 1


def test_upsert_rates_updates_changed_value_on_conflict(conn):
    first = make_df([
        {"effective_date": date(2024, 1, 2), "currency_code": "USD", "currency_name": "dolar amerykanski", "mid_rate": 4.0},
    ])
    second = make_df([
        {"effective_date": date(2024, 1, 2), "currency_code": "USD", "currency_name": "dolar amerykanski", "mid_rate": 4.1},
    ])

    upsert_rates(conn, first)
    upsert_rates(conn, second)

    with conn.cursor() as cur:
        cur.execute("select mid_rate from exchange_rates where currency_code = 'USD'")
        (mid_rate,) = cur.fetchone()
    assert float(mid_rate) == 4.1
