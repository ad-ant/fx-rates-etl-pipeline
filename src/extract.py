"""Extract step: fetch raw FX rates from the NBP Web API (table A)."""

from datetime import date, timedelta

import requests

BASE_URL = "https://api.nbp.pl/api/exchangerates/tables/A"
MAX_CHUNK_DAYS = 93
REQUEST_TIMEOUT = 30


def split_date_range(
    start: date, end: date, max_days: int = MAX_CHUNK_DAYS
) -> list[tuple[date, date]]:
    """Split start..end (inclusive) into consecutive chunks of at most max_days days."""
    if start > end:
        raise ValueError(f"start {start} is after end {end}")

    chunks = []
    chunk_start = start
    while chunk_start <= end:
        chunk_end = min(chunk_start + timedelta(days=max_days - 1), end)
        chunks.append((chunk_start, chunk_end))
        chunk_start = chunk_end + timedelta(days=1)
    return chunks


def fetch_rates_for_range(start: date, end: date) -> list[dict]:
    """Fetch NBP table A rates for start..end in API-compatible chunks."""
    tables = []
    for chunk_start, chunk_end in split_date_range(start, end):
        url = f"{BASE_URL}/{chunk_start}/{chunk_end}/?format=json"
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 404:
            continue
        response.raise_for_status()
        tables.extend(response.json())
    return tables