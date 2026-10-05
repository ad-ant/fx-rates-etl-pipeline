"""Connection to the local Postgres instance (see docker-compose.yml)."""

import psycopg

DSN = "postgresql://fx_user:fx_password@localhost:5432/fx_rates"


def get_connection() -> psycopg.Connection:
    return psycopg.connect(DSN)
