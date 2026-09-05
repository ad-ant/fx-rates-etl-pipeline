from datetime import date

from src.transform import RATE_COLUMNS, parse_rates_response

SAMPLE_RESPONSE = [
    {
        "table": "A",
        "no": "001/A/NBP/2024",
        "effectiveDate": "2024-01-02",
        "rates": [
            {"currency": "dolar amerykański", "code": "USD", "mid": 3.9432},
            {"currency": "euro", "code": "EUR", "mid": 4.3434},
        ],
    },
    {
        "table": "A",
        "no": "002/A/NBP/2024",
        "effectiveDate": "2024-01-03",
        "rates": [
            {"currency": "dolar amerykański", "code": "USD", "mid": 3.9583},
        ],
    },
]


def test_parse_rates_response_flattens_every_rate():
    df = parse_rates_response(SAMPLE_RESPONSE)

    assert list(df.columns) == RATE_COLUMNS
    assert len(df) == 3


def test_parse_rates_response_maps_fields():
    df = parse_rates_response(SAMPLE_RESPONSE)
    first = df.iloc[0]

    assert first["effective_date"] == date(2024, 1, 2)
    assert first["currency_code"] == "USD"
    assert first["currency_name"] == "dolar amerykański"
    assert first["mid_rate"] == 3.9432


def test_parse_rates_response_empty_input_returns_empty_frame():
    df = parse_rates_response([])

    assert list(df.columns) == RATE_COLUMNS
    assert df.empty
