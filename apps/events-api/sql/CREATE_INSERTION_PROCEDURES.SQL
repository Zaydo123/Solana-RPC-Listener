/*
Procedure to insert a new token and associated data (price, volume, ownership) transactionally
*/
CREATE OR REPLACE PROCEDURE insert_token_data (
    p_publickey TEXT,
    p_metadata JSONB,
    p_realsupply NUMERIC,
    p_supply NUMERIC,
    p_decimals INT,
    p_numberofbuys BIGINT,
    p_numberofsells BIGINT,
    p_freezeauthority TEXT,
    p_mintauthority TEXT,
    p_basepoolaccount TEXT,
    p_quotepoolaccount TEXT,
    p_owner TEXT,
    p_isinitialized BOOLEAN,
    p_ipo TIMESTAMPTZ,
    p_lastupdated TIMESTAMPTZ,
    p_totalbuyvolume NUMERIC,
    p_totalsellvolume NUMERIC,
    p_totalburned NUMERIC,
    p_price NUMERIC,
    p_pricetimestamp TIMESTAMPTZ,
    p_holders JSONB
)
LANGUAGE plpgsql
AS $$
DECLARE
    token_id BIGINT;
BEGIN
    -- Start the transaction block
    BEGIN

        -- Insert into the token table (or do nothing if it already exists)
        INSERT INTO token (
            publickey, metadata, realsupply, supply, decimals, numberofbuys, numberofsells,
            freezeauthority, mintauthority, basepoolaccount, quotepoolaccount, owner,
            totalbuyvolume, totalsellvolume, totalburned, isinitialized, ipo, lastupdated
        )
        VALUES (
            p_publickey, p_metadata, p_realsupply, p_supply, p_decimals, p_numberofbuys, p_numberofsells,
            p_freezeauthority, p_mintauthority, p_basepoolaccount, p_quotepoolaccount, p_owner,
            p_totalbuyvolume, p_totalsellvolume, p_totalburned, p_isinitialized, p_ipo, p_lastupdated
        )
        ON CONFLICT (publickey) DO NOTHING;

        -- Fetch the token id
        SELECT id INTO token_id FROM token WHERE publickey = p_publickey;

        -- Call the procedure to insert the price
        PERFORM insert_token_price(token_id, p_price, p_pricetimestamp);

        -- Call the procedure to insert holders
        PERFORM insert_token_holders(token_id, p_holders);

        -- Call the procedure to insert the initial volume period (0 buy/sell volume)
        PERFORM insert_initial_volume(token_id, p_ipo);

    -- If everything was successful, commit the transaction
    EXCEPTION
        WHEN OTHERS THEN
            -- In case of any error, roll back the transaction
            ROLLBACK;
            RAISE; -- Raise the exception to signal the error
    END;
END $$;





--------------------------




/*
Procedure to insert the price for a token
*/
CREATE OR REPLACE PROCEDURE insert_token_price (
    p_tokenid BIGINT,
    p_price NUMERIC,
    p_pricetimestamp TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Insert the price data for the token
    INSERT INTO price (tokenid, price, timestamp)
    VALUES (p_tokenid, p_price, p_pricetimestamp)
    ON CONFLICT (tokenid, timestamp) DO NOTHING;
END $$;





--------------------------





/*
Procedure to insert holders for a token from a JSON array
*/
CREATE OR REPLACE PROCEDURE insert_token_holders (
    p_tokenid BIGINT,
    p_holders JSONB
)
LANGUAGE plpgsql
AS $$
DECLARE
    holder JSONB;
    holder_address TEXT;
    holder_amount NUMERIC;
    holder_timestamp TIMESTAMPTZ;
BEGIN
    -- Loop through each holder in the holders JSON array
    FOR holder IN SELECT * FROM jsonb_array_elements(p_holders) LOOP
        -- Extract the holder data
        holder_address := holder->>'holder';
        holder_amount := (holder->>'amount')::NUMERIC;
        holder_timestamp := NOW(); -- Assuming the timestamp is now

        -- Insert into the largestholder table
        INSERT INTO largestholder (tokenid, holder, amount, timestamp)
        VALUES (p_tokenid, holder_address, holder_amount, holder_timestamp)
        ON CONFLICT (tokenid, holder, timestamp) DO NOTHING;
    END LOOP;
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
    p_totalvolume NUMERIC,
    p_buyvolume NUMERIC,
    p_sellvolume NUMERIC,
    p_timestamp TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
DECLARE
    token_id BIGINT;
BEGIN
    -- Fetch the token ID based on the public key
    SELECT id INTO token_id FROM token WHERE publickey = p_publickey;

    -- Update the token's total volume, total buy/sell volume in the token table
    UPDATE token
    SET 
        totalbuyvolume = totalbuyvolume + p_buyvolume,
        totalsellvolume = totalsellvolume + p_sellvolume,
        totalsellvolume = p_totalvolume  -- Update the total volume with new value
    WHERE id = token_id;

    -- Insert or update the volume period for the token
    INSERT INTO volumeperiods (tokenid, buyvolume, sellvolume, periodstart)
    VALUES (token_id, p_buyvolume, p_sellvolume, p_timestamp)
    ON CONFLICT (tokenid, periodstart)
    DO UPDATE
    SET 
        buyvolume = volumeperiods.buyvolume + EXCLUDED.buyvolume,
        sellvolume = volumeperiods.sellvolume + EXCLUDED.sellvolume;
END $$;
