/*
Author:  Zayd Alzein
Date:    2024-09-12
Purpose: Create the tables for the TimescaleDB database, convert relevant tables to hypertables, and apply compression policies.
*/

/*
-- Table for storing token information
CREATE TABLE IF NOT EXISTS Token (
    id TEXT PRIMARY KEY,  -- Token ID
    publickey TEXT UNIQUE,
    metadata JSON,
    realSupply BIGINT,
    supply NUMERIC(65,30),
    decimals INT,
    numberOfBuys BIGINT DEFAULT 0,
    numberOfSells BIGINT DEFAULT 0,
    freezeAuthority TEXT,
    mintAuthority TEXT,
    basePoolAccount TEXT,
    quotePoolAccount TEXT,
    owner TEXT,
    totalBuyVolume NUMERIC(65,30), -- Nullable because set after tracking ends
    totalSellVolume NUMERIC(65,30), -- Nullable because set after tracking ends
    totalBurned NUMERIC(65,30),
    isInitialized BOOLEAN,
    ipo TIMESTAMPTZ,  -- Changed to TIMESTAMPTZ for best practices
    lastUpdated TIMESTAMPTZ,  -- Changed to TIMESTAMPTZ
    lastCacheUpdate TIMESTAMPTZ DEFAULT now()  -- Changed to TIMESTAMPTZ
);

-- Table for individual holders within LargestHolders
CREATE TABLE IF NOT EXISTS LargestHolder (
    id TEXT PRIMARY KEY,
    tokenID TEXT,  -- Foreign key to Token
    holder TEXT,
    amount NUMERIC(65,30),
    CONSTRAINT fk_token_largestHolder FOREIGN KEY (tokenID) REFERENCES Token(id) ON DELETE CASCADE
);

-- Table for storing top ownership percentage
CREATE TABLE IF NOT EXISTS LargestHolders (
    id TEXT PRIMARY KEY,
    tokenID TEXT,  -- Foreign key to Token
    topOwnershipPercentage NUMERIC(65,30),
    timestamp TIMESTAMPTZ,  -- Changed to TIMESTAMPTZ
    CONSTRAINT fk_token_largestHolders FOREIGN KEY (tokenID) REFERENCES Token(id) ON DELETE CASCADE
);

-- Table for storing price data
CREATE TABLE IF NOT EXISTS Price (
    id TEXT,
    tokenID TEXT,  -- Foreign key to Token
    price NUMERIC(65,30),
    timestamp TIMESTAMPTZ,  -- Changed to TIMESTAMPTZ
    PRIMARY KEY (id, timestamp),
    CONSTRAINT fk_token_price FOREIGN KEY (tokenID) REFERENCES Token(id) ON DELETE CASCADE
);

-- Convert Price table to hypertable
SELECT create_hypertable('Price', 'timestamp', create_default_indexes => TRUE, if_not_exists => TRUE);

-- Set compression policy for Price table (compress chunks older than 2 days)
ALTER TABLE Price SET (timescaledb.compress, timescaledb.compress_segmentby = 'tokenID');
SELECT add_compression_policy('Price', INTERVAL '2 days', if_not_exists => TRUE);

-- Table for storing volume periods data
CREATE TABLE IF NOT EXISTS VolumePeriods (
    id TEXT,
    tokenID TEXT,  -- Foreign key to Token
    buyVolume NUMERIC(65,30),
    sellVolume NUMERIC(65,30),
    periodStart TIMESTAMPTZ, 
    PRIMARY KEY (id, periodStart),
    CONSTRAINT fk_token_volume FOREIGN KEY (tokenID) REFERENCES Token(id) ON DELETE CASCADE
);

-- Convert VolumePeriods table to hypertable
SELECT create_hypertable('VolumePeriods', 'periodStart', create_default_indexes => TRUE, if_not_exists => TRUE);

-- Set compression policy for VolumePeriods table (compress chunks older than 2 days)
ALTER TABLE VolumePeriods SET (timescaledb.compress, timescaledb.compress_segmentby = 'tokenID');
SELECT add_compression_policy('VolumePeriods', INTERVAL '2 days', if_not_exists => TRUE);

-- Table for storing burn periods data
CREATE TABLE IF NOT EXISTS BurnPeriods (
    id TEXT,
    tokenID TEXT,  -- Foreign key to Token
    amount NUMERIC(65,30),
    periodStart TIMESTAMPTZ, 
    PRIMARY KEY (id, periodStart),
    CONSTRAINT fk_token_burn FOREIGN KEY (tokenID) REFERENCES Token(id) ON DELETE CASCADE
);

-- Convert BurnPeriods table to hypertable
SELECT create_hypertable('BurnPeriods', 'periodStart', create_default_indexes => TRUE, if_not_exists => TRUE);

-- Set compression policy for BurnPeriods table (compress chunks older than 2 days)
ALTER TABLE BurnPeriods SET (timescaledb.compress, timescaledb.compress_segmentby = 'tokenID');
SELECT add_compression_policy('BurnPeriods', INTERVAL '2 days', if_not_exists => TRUE);
*/