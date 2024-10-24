/*
Author:  Zayd Alzein
Date:    2024-09-12
*/

/* Enable the TimescaleDB extension */
CREATE EXTENSION IF NOT EXISTS timescaledb;

/* Table for storing token information */
CREATE TABLE IF NOT EXISTS token (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    publickey TEXT UNIQUE NOT NULL,
    metadata JSONB,
    realsupply BIGINT,
    supply NUMERIC(38, 18),
    decimals INT NOT NULL,
    numberofbuys BIGINT DEFAULT 0,
    numberofsells BIGINT DEFAULT 0,
    freezeauthority TEXT,
    mintauthority TEXT,
    basepoolaccount TEXT,
    quotepoolaccount TEXT,
    owner TEXT,
    totalbuyvolume NUMERIC(38, 18),
    totalsellvolume NUMERIC(38, 18),
    totalburned NUMERIC(38, 18),
    isinitialized BOOLEAN NOT NULL,
    ipo TIMESTAMPTZ,
    lastupdated TIMESTAMPTZ,
    lastcacheupdate TIMESTAMPTZ DEFAULT NOW()
);

/* Table for storing individual holder's data (including changes over time) */
CREATE TABLE IF NOT EXISTS largestholder (
    tokenid BIGINT NOT NULL,     -- Foreign key to token table
    holder TEXT NOT NULL,        -- Individual holder's public address
    amount NUMERIC(38, 18) NOT NULL, -- High precision token amount
    timestamp TIMESTAMPTZ NOT NULL,  -- Time of snapshot
    CONSTRAINT pk_largestholder PRIMARY KEY (tokenid, holder, timestamp),
    CONSTRAINT fk_token_largestholder FOREIGN KEY (tokenid) REFERENCES token(id) ON DELETE CASCADE
);

/* Convert largestholder table to hypertable */
SELECT create_hypertable(
    'largestholder',
    'timestamp',
    chunk_time_interval => INTERVAL '7 days', -- Increase chunk size for better scaling
    create_default_indexes => TRUE,
    if_not_exists => TRUE
);

/* Set compression policy for largestholder table */
ALTER TABLE largestholder SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'tokenid, holder',
    timescaledb.compress_orderby = 'timestamp DESC'
);
SELECT add_compression_policy('largestholder', INTERVAL '1 day', if_not_exists => TRUE);


/* Table for storing price data */
CREATE TABLE IF NOT EXISTS price (
    tokenid BIGINT NOT NULL,
    price NUMERIC(38, 18),
    timestamp TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_price PRIMARY KEY (tokenid, timestamp),
    CONSTRAINT fk_token_price FOREIGN KEY (tokenid) REFERENCES token(id) ON DELETE CASCADE
);

/* Convert price table to hypertable */
SELECT create_hypertable(
    'price',
    'timestamp',
    chunk_time_interval => INTERVAL '7 days', -- Adjust chunk size to weekly
    create_default_indexes => TRUE,
    if_not_exists => TRUE
);

/* Set compression policy for price table */
ALTER TABLE price SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'tokenid',
    timescaledb.compress_orderby = 'timestamp DESC'
);
SELECT add_compression_policy('price', INTERVAL '1 day', if_not_exists => TRUE);


/* Table for storing volume periods data */
CREATE TABLE IF NOT EXISTS volumeperiods (
    tokenid BIGINT NOT NULL,
    buyvolume NUMERIC(38, 18),
    sellvolume NUMERIC(38, 18),
    periodstart TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_volumeperiods PRIMARY KEY (tokenid, periodstart),
    CONSTRAINT fk_token_volume FOREIGN KEY (tokenid) REFERENCES token(id) ON DELETE CASCADE
);

/* Convert volumeperiods table to hypertable */
SELECT create_hypertable(
    'volumeperiods',
    'periodstart',
    chunk_time_interval => INTERVAL '7 days', -- Adjust chunk size to weekly
    create_default_indexes => TRUE,
    if_not_exists => TRUE
);

/* Set compression policy for volumeperiods table */
ALTER TABLE volumeperiods SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'tokenid',
    timescaledb.compress_orderby = 'periodstart DESC'
);
SELECT add_compression_policy('volumeperiods', INTERVAL '1 day', if_not_exists => TRUE);


/* Table for storing burn periods data */
CREATE TABLE IF NOT EXISTS burnperiods (
    tokenid BIGINT NOT NULL,
    amount NUMERIC(38, 18),
    periodstart TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_burnperiods PRIMARY KEY (tokenid, periodstart),
    CONSTRAINT fk_token_burn FOREIGN KEY (tokenid) REFERENCES token(id) ON DELETE CASCADE
);

/* Convert burnperiods table to hypertable */
SELECT create_hypertable(
    'burnperiods',
    'periodstart',
    chunk_time_interval => INTERVAL '7 days', -- Adjust chunk size to weekly
    create_default_indexes => TRUE,
    if_not_exists => TRUE
);

/* Set compression policy for burnperiods table */
ALTER TABLE burnperiods SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'tokenid',
    timescaledb.compress_orderby = 'periodstart DESC'
);
SELECT add_compression_policy('burnperiods', INTERVAL '1 day', if_not_exists => TRUE);


/* Table for storing top ownership percentage */
CREATE TABLE IF NOT EXISTS largestholders (
    tokenid BIGINT NOT NULL,
    topownershippercentage NUMERIC(7, 5),
    timestamp TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_largestholders PRIMARY KEY (tokenid, timestamp),
    CONSTRAINT fk_token_largestholders FOREIGN KEY (tokenid) REFERENCES token(id) ON DELETE CASCADE
);

/* Convert largestholders table to hypertable */
SELECT create_hypertable(
    'largestholders',
    'timestamp',
    chunk_time_interval => INTERVAL '7 days', -- Adjust chunk size to weekly
    create_default_indexes => TRUE,
    if_not_exists => TRUE
);

/* Set compression policy for largestholders table */
ALTER TABLE largestholders SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'tokenid',
    timescaledb.compress_orderby = 'timestamp DESC'
);
SELECT add_compression_policy('largestholders', INTERVAL '1 day', if_not_exists => TRUE);
