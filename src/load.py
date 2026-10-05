"""Idempotent load of FX rates into the exchange_rates table."""

from datetime import date

import pandas as pd
import psycopg

UPSERT_SQL = """
insert into exchange_rates (effective_date, currency_code, currency_name, mid_rate)
values (%(effective_date)s, %(currency_code)s, %(currency_name)s, %(mid_rate)s)
on conflict (effective_date, currency_code)
do update set
    currency_name = excluded.currency_name,
    mid_rate = excluded.mid_rate,
    loaded_at = now()
"""


def upsert_rates(conn: psycopg.Connection, df: pd.DataFrame) -> None:
    """Insert new rows or update existing ones, keyed on (effective_date, currency_code)."""
    if df.empty:
        return
    with conn.cursor() as cur:
        cur.executemany(UPSERT_SQL, df.to_dict("records"))
    conn.commit()


def get_last_loaded_date(conn: psycopg.Connection) -> date | None:
    """Return the most recent effective_date in the table, or None if it's empty."""
    with conn.cursor() as cur:
        cur.execute("select max(effective_date) from exchange_rates")
        (last_date,) = cur.fetchone()
    return last_date
