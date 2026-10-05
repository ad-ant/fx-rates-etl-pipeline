import re
import warnings

import pandas as pd

CURRENCY_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")
MIN_CURRENCIES_PER_DAY = 20

CRITICAL_COLUMNS = ["effective_date", "currency_code", "currency_name", "mid_rate"]
KEY_COLUMNS = ["effective_date", "currency_code"]


def validate_rates(df: pd.DataFrame) -> None:
    """Raise ValueError on violations that make a batch unsafe to load."""
    if df.empty:
        return

    if df[CRITICAL_COLUMNS].isnull().any().any():
        raise ValueError("null values in critical columns")

    if (df["mid_rate"] < 0).any():
        raise ValueError("negative mid_rate")

    bad_codes = df.loc[~df["currency_code"].str.match(CURRENCY_CODE_PATTERN), "currency_code"]
    if not bad_codes.empty:
        raise ValueError(f"invalid currency_code format: {sorted(bad_codes.unique())}")

    if df.duplicated(subset=KEY_COLUMNS).any():
        raise ValueError("duplicate (effective_date, currency_code) in batch")

    counts_per_day = df.groupby("effective_date")["currency_code"].nunique()
    low_days = counts_per_day[counts_per_day < MIN_CURRENCIES_PER_DAY]
    if not low_days.empty:
        warnings.warn(f"low currency count for dates: {list(low_days.index)}")
