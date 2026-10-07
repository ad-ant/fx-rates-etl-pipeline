import argparse
from datetime import date

import pandas as pd
from prefect import flow, task
from prefect.schedules import Cron

from src.db import get_connection
from src.extract import fetch_rates_for_range
from src.load import get_last_loaded_date, upsert_rates
from src.quality import validate_rates
from src.transform import parse_rates_response
from src.watermark import get_load_window

DEFAULT_START = date(2024, 1, 1)
# nbp publishes table A around midday on business days
SCHEDULE_CRON = "30 12 * * 1-5"
SCHEDULE_TIMEZONE = "Europe/Warsaw"


@task
def get_last_loaded_date_task() -> date | None:
    with get_connection() as conn:
        return get_last_loaded_date(conn)


@task(retries=2, retry_delay_seconds=30)
def extract_task(start: date, end: date) -> list[dict]:
    return fetch_rates_for_range(start, end)


@task
def transform_task(raw_json: list[dict]) -> pd.DataFrame:
    return parse_rates_response(raw_json)


@task
def validate_task(df: pd.DataFrame) -> None:
    validate_rates(df)


@task
def load_task(df: pd.DataFrame) -> None:
    with get_connection() as conn:
        upsert_rates(conn, df)


@flow(name="fx-rates-etl", log_prints=True)
def fx_rates_flow() -> None:
    last_loaded_date = get_last_loaded_date_task()
    window = get_load_window(last_loaded_date, date.today(), DEFAULT_START)
    if window is None:
        print(f"nothing to load, last loaded date is {last_loaded_date}")
        return

    start, end = window
    raw_json = extract_task(start, end)
    df = transform_task(raw_json)
    validate_task(df)
    load_task(df)
    print(f"loaded {len(df)} rows for {start}..{end}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load NBP table A FX rates into Postgres.")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help=f"run on cron '{SCHEDULE_CRON}' ({SCHEDULE_TIMEZONE}) instead of once",
    )
    args = parser.parse_args()

    if args.schedule:
        schedule = Cron(SCHEDULE_CRON, timezone=SCHEDULE_TIMEZONE)
        fx_rates_flow.serve(name="fx-rates-daily", schedule=schedule)
    else:
        fx_rates_flow()
