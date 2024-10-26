/*
Procedure to insert a new token and associated data (price, volume, ownership) transactionally
*/
CREATE OR REPLACE PROCEDURE insert_token_data (
    p_publickey TEXT,
    p_metadata JSONB,
    p_realsupply NUMERIC,
    p_supply NUMERIC,
    p_decimals INT,
    p_freezeauthority TEXT,
    p_mintauthority TEXT,
    p_basepoolaccount TEXT,
    p_quotepoolaccount TEXT,
    p_owner TEXT,
    p_isinitialized BOOLEAN,
    p_ipo DOUBLE PRECISION, -- IPO time as double precision (Unix timestamp)
    p_lastupdated DOUBLE PRECISION, -- Last updated as double precision (Unix timestamp)
    p_totalbuyvolume NUMERIC,
    p_totalsellvolume NUMERIC,
    p_totalburned NUMERIC,
    p_price NUMERIC,
    p_pricetimestamp DOUBLE PRECISION, -- Price timestamp as double precision (Unix timestamp)
    p_holders JSONB
)
LANGUAGE plpgsql
AS $$
DECLARE
    token_id BIGINT;
    top_ownership_percent NUMERIC;
BEGIN    

        -- Insert into the token table (or do nothing if it already exists)
        INSERT INTO token (
            publickey, metadata, realsupply, supply, decimals,
            freezeauthority, mintauthority, basepoolaccount, quotepoolaccount, owner,
            totalbuyvolume, totalsellvolume, totalburned, isinitialized, ipo, lastupdated
        )
        VALUES (
            p_publickey, p_metadata, p_realsupply, p_supply, p_decimals,
            p_freezeauthority, p_mintauthority, p_basepoolaccount, p_quotepoolaccount, p_owner,
            p_totalbuyvolume, p_totalsellvolume, p_totalburned, p_isinitialized, to_timestamp(p_ipo)::TIMESTAMPTZ, 
            to_timestamp(p_lastupdated)::TIMESTAMPTZ
        )
        ON CONFLICT (publickey) DO NOTHING;

        -- Fetch the token id
        SELECT id INTO token_id FROM token WHERE publickey = p_publickey;


        -- if  price is not -1 then insert the price
        IF p_price != -1 THEN
            -- Call the procedure to insert the price
            CALL insert_token_price(p_publickey, p_price, p_pricetimestamp);
        END IF;

        SELECT ROUND((p_holders->0->>'topOwnershipPercentage')::NUMERIC, 4) INTO top_ownership_percent;

        IF top_ownership_percent = 100 THEN
            top_ownership_percent := 100.0000;
        END IF;

        IF top_ownership_percent IS NOT NULL THEN
            CALL insert_token_holders(p_publickey, p_holders, top_ownership_percent, p_pricetimestamp);
        END IF;

        -- Call the procedure to insert the initial volume period (0 buy/sell volume)
        CALL insert_initial_volume(token_id, to_timestamp(p_ipo)::TIMESTAMPTZ);

END $$;




--------------------------

CREATE OR REPLACE PROCEDURE set_last_updated (
    p_publickey TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Update the last updated timestamp for the token
    UPDATE token
    SET lastupdated = NOW()
    WHERE publickey = p_publickey;
END $$;

--------------------------

/*
Procedure to insert the price for a token
*/
CREATE OR REPLACE PROCEDURE insert_token_price (
    p_publickey TEXT,
    p_price NUMERIC,
    p_pricetimestamp DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
DECLARE
    token_id BIGINT;
BEGIN
    -- Fetch the token ID based on the public key
    SELECT id INTO token_id FROM token WHERE publickey = p_publickey;

    -- if NULL raise an exception 
    IF token_id IS NULL THEN
        RAISE EXCEPTION 'Token with public key %% not found', p_publickey;
    END IF;

    -- Insert the price data for the token
    INSERT INTO price (tokenid, price, timestamp)
    VALUES (token_id, p_price, to_timestamp(p_pricetimestamp)::TIMESTAMPTZ)
    ON CONFLICT (tokenid, timestamp) DO NOTHING;

    CALL set_last_updated(p_publickey);

END $$;



--------------------------






/*
Procedure to insert holders for a token from a JSON array
*/
CREATE OR REPLACE PROCEDURE insert_token_holders (
    p_publickey TEXT,
    p_holders JSONB,
    p_top_ownership_percent NUMERIC,
    p_timestamp DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
DECLARE
    token_id BIGINT;
    holder_data JSONB;
    holder_address TEXT;
    holder_amount NUMERIC;
    holder_timestamp TIMESTAMPTZ;
BEGIN
    -- Fetch the token ID based on the public key
    SELECT id INTO token_id FROM token WHERE publickey = p_publickey;

    -- If token_id is NULL, raise an exception 
    IF token_id IS NULL THEN
        RAISE EXCEPTION 'Token with public key %% not found', p_publickey;
    END IF;

    -- Insert the top ownership percentage into the largestholders table
    INSERT INTO largestholders (tokenid, topownershippercentage, timestamp)
    VALUES (token_id, p_top_ownership_percent, to_timestamp(p_timestamp)::TIMESTAMPTZ)
    ON CONFLICT (tokenid, timestamp) DO NOTHING;

    -- Loop through each holder in the JSONB array
    -- Since the holders are within a JSON array inside the "holders" key, access it properly
    FOR holder_data IN SELECT * FROM jsonb_array_elements(p_holders->'holders') LOOP
        -- Extract the holder data
        holder_address := holder_data->>'holder';
        holder_amount := COALESCE((holder_data->>'amount')::NUMERIC, 0);  -- Ensure numeric conversion
        holder_timestamp := to_timestamp(p_timestamp)::TIMESTAMPTZ;

        -- Insert into the largestholder table
        INSERT INTO largestholder (tokenid, holder, amount, timestamp)
        VALUES (token_id, holder_address, holder_amount, holder_timestamp)
        ON CONFLICT (tokenid, holder, timestamp) DO NOTHING;
    END LOOP;
    
    -- Call the procedure to set the last updated timestamp
    CALL set_last_updated(p_publickey);

END $$;













--------------------------






/*
Procedure to insert the initial volume period for a token with 0 buy/sell volume
*/
CREATE OR REPLACE PROCEDURE insert_initial_volume (
    p_tokenid BIGINT,
    p_ipo TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Insert the initial volume period with 0 buy/sell volume
    INSERT INTO volumeperiods (tokenid, buyvolume, sellvolume, periodstart)
    VALUES (p_tokenid, 0, 0, p_ipo)
    ON CONFLICT (tokenid, periodstart) DO NOTHING;
END $$;


--------------------------



/*
Procedure to update the volume for a token based on Kafka message data
*/
CREATE OR REPLACE PROCEDURE update_token_volume (
    p_publickey TEXT,
    p_buyvolume NUMERIC,
    p_sellvolume NUMERIC,
    p_timestamp DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
DECLARE
    token_id BIGINT;
BEGIN
    -- Fetch the token ID based on the public key
    SELECT id INTO token_id FROM token WHERE publickey = p_publickey;

    -- if NULL raise an exception 
    IF token_id IS NULL THEN
        RAISE EXCEPTION 'Token with public key %% not found', p_publickey;
    END IF;

    -- Update the token's total volume, total buy/sell volume in the token table
    UPDATE token
    SET 
        totalbuyvolume = totalbuyvolume + p_buyvolume,
        totalsellvolume = totalsellvolume + p_sellvolume
    WHERE id = token_id;

    -- Insert or update the volume period for the token, cast timestamp to TIMESTAMPTZ
    INSERT INTO volumeperiods (tokenid, buyvolume, sellvolume, periodstart)
    VALUES (token_id, p_buyvolume, p_sellvolume, to_timestamp(p_timestamp)::TIMESTAMPTZ)
    ON CONFLICT (tokenid, periodstart)
    DO UPDATE
    SET 
        buyvolume = volumeperiods.buyvolume + EXCLUDED.buyvolume,
        sellvolume = volumeperiods.sellvolume + EXCLUDED.sellvolume;

    CALL set_last_updated(p_publickey);


END $$;
