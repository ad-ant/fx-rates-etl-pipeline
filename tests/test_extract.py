from datetime import date, timedelta

import pytest
import requests

from src.extract import MAX_CHUNK_DAYS, fetch_rates_for_range, split_date_range


def test_split_date_range_short_range_is_one_chunk():
    start, end = date(2024, 1, 1), date(2024, 1, 10)
    assert split_date_range(start, end) == [(start, end)]


def test_split_date_range_long_range_is_split_without_gaps():
    start, end = date(2024, 1, 1), date(2024, 12, 31)
    chunks = split_date_range(start, end)

    assert len(chunks) > 1
    assert chunks[0][0] == start
    assert chunks[-1][1] == end
    for (_, prev_end), (next_start, _) in zip(chunks, chunks[1:]):
        assert next_start == prev_end + timedelta(days=1)
    for chunk_start, chunk_end in chunks:
        assert (chunk_end - chunk_start).days + 1 <= MAX_CHUNK_DAYS


def test_split_date_range_rejects_reversed_range():
    with pytest.raises(ValueError):
        split_date_range(date(2024, 2, 1), date(2024, 1, 1))


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


def test_fetch_rates_for_range_treats_404_as_empty(monkeypatch):
    monkeypatch.setattr(
        "src.extract.requests.get", lambda url, timeout=None: FakeResponse(404)
    )
    assert fetch_rates_for_range(date(2024, 1, 6), date(2024, 1, 7)) == []


def test_fetch_rates_for_range_concatenates_chunks(monkeypatch):
    calls = []

    def fake_get(url, timeout=None):
        calls.append(url)
        return FakeResponse(200, [{"effectiveDate": f"call-{len(calls)}", "rates": []}])

    monkeypatch.setattr("src.extract.requests.get", fake_get)

    result = fetch_rates_for_range(date(2024, 1, 1), date(2024, 7, 20))
    assert len(calls) > 1
    assert len(result) == len(calls)