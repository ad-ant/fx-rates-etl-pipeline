from datetime import date

import pandas as pd

RATE_COLUMNS = ["effective_date", "currency_code", "currency_name", "mid_rate"]


def parse_rates_response(raw_json: list[dict]) -> pd.DataFrame:
    """Flatten the NBP table A payload into one row per (effective_date, currency)."""
    records = []
    for table in raw_json:
        effective_date = date.fromisoformat(table["effectiveDate"])
        for rate in table["rates"]:
            records.append(
                {
                    "effective_date": effective_date,
                    "currency_code": rate["code"],
                    "currency_name": rate["currency"],
                    "mid_rate": rate["mid"],
                }
            )
    return pd.DataFrame(records, columns=RATE_COLUMNS)
