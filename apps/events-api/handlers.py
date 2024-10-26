import database
import json
import logging
import os
import sys
from dotenv import find_dotenv, load_dotenv
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")

"""

    Environment variables

"""

load_dotenv(find_dotenv(".env"))
required_env_vars = ["POSTGRES_HOST","POSTGRES_PORT","POSTGRES_USER","POSTGRES_PASSWORD","POSTGRES_SSL_MODE"]
missing_env_vars = [env_var for env_var in required_env_vars if not os.getenv(env_var)]
if len(missing_env_vars) > 0:
    logging.error(f"Missing environment variables: {missing_env_vars}")
    sys.exit(1)

"""
    Database connection
"""

dbconfig = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "db": os.getenv("POSTGRES_DB"),
    "username": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "schema": os.getenv("POSTGRES_SCHEMA"),
    "ssl": os.getenv("POSTGRES_SSL_MODE")
}

DB = database.Database(**dbconfig)
logging.info("Creating tables")
DB.create_tables()
DB.conn_still_alive()


logging.info("Creating insertion procedures")
DB.create_insertion_procedures()


"""
    Handlers for each event type
"""

# Handler for token events (Inserts token data into the database)
async def store_token(data: dict):
    try:
        public_key = data["PublicKey"]
        metadata = json.dumps(data["Metadata"])  # Assuming metadata is a dictionary
        real_supply = data["RealSupply"]
        supply = data["Supply"]
        decimals = data["Decimals"]
        number_of_buys = data["NumberOfBuys"]
        number_of_sells = data["NumberOfSells"]
        freeze_authority = data["FreezeAuthority"]
        mint_authority = data["MintAuthority"]
        base_pool_account = data["BasePoolAccount"]
        quote_pool_account = data["QuotePoolAccount"]
        owner = data["Owner"]
        is_initialized = data["IsInitialized"]
        ipo_time = data["IPO"] / 1000  # Convert IPO timestamp from milliseconds to seconds
        last_updated = data["LastUpdated"] / 1000  # Convert to seconds
        total_buy_volume = data["TotalVolume"]["TotalBuyVolume"]
        total_sell_volume = data["TotalVolume"]["TotalSellVolume"]
        total_burned = data["TotalBurned"]
        price = float(data["Prices"][0]["price"])  # Assuming prices list is always present
        price_time = data["Prices"][0]["time"] / 1000  # Convert price timestamp to seconds
        holders = json.dumps(data["LargestHolders"])  # Assuming LargestHolders is a list of holders
        
        # Call the database procedure to insert the token data
        DB.call_procedure(
            "insert_token_data",
            [
                "TEXT", "JSONB", "NUMERIC", "INT", "BIGINT", "BIGINT", "TEXT", "TEXT", 
                "TEXT", "TEXT", "TEXT", "BOOLEAN", "PRECISION", "DOUBLE PRECISION", 
                "NUMERIC", "NUMERIC", "NUMERIC", "NUMERIC", "DOUBLE PRECISION", "JSONB"
            ], 
            public_key, metadata, real_supply, supply, decimals, number_of_buys, 
            number_of_sells, freeze_authority, mint_authority, base_pool_account, 
            quote_pool_account, owner, is_initialized, ipo_time, last_updated, 
            total_buy_volume, total_sell_volume, total_burned, price, price_time, holders
        )
        logging.info(f"Inserted token: {public_key}")
        
    except Exception as e:
        logging.error(f"Error in storing token: {e}")
        logging.error(f"Type: {type(e)}")
        raise


# Handler for price events (Inserts price data into the database)
async def store_price(data: dict):
    try:
        public_key = data["tokenAddress"]
        price = float(data["price"])
        timestamp = data["time"] / 1000  # Convert to seconds
        
        # Fetch the token ID (or some mapping of tokenAddress to the token table's ID)
        DB.call_procedure("insert_token_price", ["TEXT", "NUMERIC", "DOUBLE PRECISION"], public_key, price, timestamp)
        logging.info(f"Inserted price for token: {public_key}")
        
    except Exception as e:
        logging.error(f"Error in storing price: {e}")
        raise

# Handler for volume events (Inserts or updates volume data into the database)
async def store_volume(data: dict):
    try:
        public_key = data["tokenAddress"]
        buy_volume = float(data["totalBuyVolume"])
        sell_volume = float(data["totalSellVolume"])
        timestamp = data["time"] / 1000  # Convert to seconds
        
        # Call the volume update procedure
        DB.call_procedure("update_token_volume", ["TEXT","NUMERIC","NUMERIC","DOUBLE PRECISION"], public_key, buy_volume, sell_volume, timestamp)
        logging.info(f"Updated volume for token: {public_key}")
        
    except Exception as e:
        logging.error(f"Error in storing volume: {e}")
        raise

# Handler for top holders events (Inserts top holders data into the database)
async def store_top_holders(data: dict):
    try:
        public_key = data["tokenAddress"]
        holders = json.dumps(data["holders"])  # Convert holders to JSON format
        timestamp = data["timestamp"] / 1000  # Convert to seconds
        
        # Call the holder insertion procedure
        DB.call_procedure("insert_token_holders", ["TEXT","JSONB"],public_key, holders, timestamp)
        logging.info(f"Inserted top holders for token: {public_key}")
        
    except Exception as e:
        logging.error(f"Error in storing top holders: {e}")
        raise
