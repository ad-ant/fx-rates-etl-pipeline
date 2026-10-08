# fx-rates-etl-pipeline
A small ETL pipeline that loads daily exchange rates from the National Bank of Poland (NBP) into Postgres. It runs with Prefect, loads only days after the last one it already has, and can be re-run safely without creating duplicates.

## Why NBP
The NBP API is free, needs no key, and publishes one table of rates (table A, ~32 currencies) per business day. It also has two limits the pipeline has to handle:
- one request can cover at most 93 days
- a range with no published table (e.g. a weekend) returns 404

## How it works
1. Read the last loaded date from the table, i.e. `MAX(effective_date)` (`load.py`).
2. Work out the missing window: from the day after that date until today. On an empty table, start from 2024-01-01 (`watermark.py`).
3. Fetch rates for that window from the API, in chunks of up to 93 days. 404 means no data, not an error (`extract.py`).
4. Turn the response into one row per date and currency (`transform.py`).
5. Validate the batch (`quality.py`).
6. Upsert into `exchange_rates` (`load.py`).

Prefect wires these steps together in `flow.py`.

## Data quality checks
The batch is rejected if it has:
- nulls in date, code, name or rate
- a negative rate
- a currency code that isn't 3 capital letters
- the same date + currency twice

If a day has fewer than 20 currencies, the pipeline only warns.

## Incremental loading and idempotency
**Incremental:** there's no separate state table. The next run starts from `MAX(effective_date) + 1 day`. If the table already has today's rates, the flow stops without calling the API.

**Idempotent:** the table's primary key is `(effective_date, currency_code)` and loading uses `INSERT ... ON CONFLICT DO UPDATE`. Loading the same data again updates the existing rows instead of adding new ones.

A failed run doesn't leave a gap: the whole batch is committed in one transaction, so if a run fails, the last loaded date doesn't move and the next run tries the same window again.

## Running it
Requires Python 3.12 and Docker.

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

docker compose up -d
python -m pytest
python -m src.flow
```

To run it every weekday at 12:30 (Warsaw time), start a Prefect server in a separate terminal first. Without one, Prefect can't schedule runs:

```
prefect server start
```

```
export PREFECT_API_URL=http://127.0.0.1:4200/api
python -m src.flow --schedule
```

## Results
- After the backfill: 22,839 rows, 2024-01-02 to 2026-10-07 (698 business days).
- Running it again the same day: `nothing to load`.
- Deleted the last week (160 rows) and ran again: the flow loaded exactly those 160 rows.
- Upserted the same month (726 rows) twice: row count didn't change.

The last three are in `notebooks/01_pipeline_walkthrough.ipynb`.

## Future improvements
- CI (GitHub Actions)
- running the pipeline itself in Docker
- cloud deployment
- dbt
- alerts when a run fails
- fetching chunks in parallel