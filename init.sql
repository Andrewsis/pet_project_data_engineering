CREATE DATABASE test;

\c test;

CREATE TABLE crypto_data (
    symbol TEXT NOT NULL,
    price_change DECIMAL(20,8),
    price_change_percent DECIMAL(20,8),
    weighted_avg_price DECIMAL(20,8),
    prev_close_price DECIMAL(20,8),
    last_price DECIMAL(20,8),
    last_qty DECIMAL(20,8),
    bid_price DECIMAL(20,8),
    bid_qty DECIMAL(20,8),
    ask_price DECIMAL(20,8),
    ask_qty DECIMAL(20,8),
    open_price DECIMAL(20,8),
    high_price DECIMAL(20,8),
    low_price DECIMAL(20,8),
    volume DECIMAL(20,8),
    quote_volume DECIMAL(20,8),
    close_time TIMESTAMP,
    first_id BIGINT,
    last_id BIGINT,
    count BIGINT,
    trend BOOLEAN 
);
