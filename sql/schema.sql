-- NBP table A mid rates
create table if not exists exchange_rates (
    effective_date date not null,
    currency_code varchar(3) not null,
    currency_name text not null,
    mid_rate numeric(12, 4) not null,
    loaded_at timestamptz not null default now(),
    primary key (effective_date, currency_code)
);
