import database
import json
import logging
import os
import sys
import traceback
from dotenv import find_dotenv, load_dotenv
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

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
        freeze_authority = data["FreezeAuthority"]
        mint_authority = data["MintAuthority"]
        base_pool_account = data["BasePoolAccount"]
        quote_pool_account = data["QuotePoolAccount"]
        owner = data["Owner"]
        is_initialized = data["IsInitialized"]
        ipo_time = data["IPO"]  # Convert IPO timestamp from milliseconds to seconds
        last_updated = data["LastUpdated"] / 1000  # Convert to seconds
        total_buy_volume = data["TotalVolume"]["TotalBuyVolume"]
        total_sell_volume = data["TotalVolume"]["TotalSellVolume"]
        total_burned = data["TotalBurned"]



        prices = data.get("Prices", None)
        if prices is None:
            price = -1
            price_time = -1
        else:
            price = prices[0].get("price", -1)
            price_time = prices[0].get("time", -1)


        holders = data.get("LargestHolders", [])  # Assuming LargestHolders is a list of holders
        if holders is None:
            holders = []
        else:
            holders = json.dumps(holders[0].get("holders", []))  # Assuming holders is a list of dictionaries
        logging.info(holders)

        # Call the database procedure to insert the token data
        DB.call_procedure(
            "insert_token_data",
            [
                "TEXT", "JSONB", "NUMERIC", "NUMERIC","INT", "TEXT", "TEXT", 
                "TEXT", "TEXT", "TEXT", "BOOLEAN", "DOUBLE PRECISION", "DOUBLE PRECISION", 
                "NUMERIC", "NUMERIC", "NUMERIC", "NUMERIC", "DOUBLE PRECISION", "JSONB"
            ], 
            public_key, metadata, real_supply, supply, decimals, freeze_authority, mint_authority, base_pool_account, 
            quote_pool_account, owner, is_initialized, ipo_time, last_updated, 
            total_buy_volume, total_sell_volume, total_burned, price, price_time, holders
        )
        
    except Exception as e:
        # use traceback to get the full error
        logging.error(f"Error in storing token: {traceback.format_exc()}")
        raise



# Handler for price events (Inserts price data into the database)
async def store_price(data: dict):
    try:
        public_key = data["tokenAddress"]
        price = float(data["price"])
        timestamp = data["time"] / 1000  # Convert to seconds
        
        # Fetch the token ID (or some mapping of tokenAddress to the token table's ID)
        DB.call_procedure("insert_token_price", ["TEXT", "NUMERIC", "DOUBLE PRECISION"], public_key, price, timestamp)
        
    except Exception as e:
        logging.error(f"Error in storing price: {e}")
        raise

# Handler for volume events (Inserts or updates volume data into the database)
async def store_volume(data: dict):
    try:
        public_key = data["tokenAddress"]
        buy_volume = float(data["totalBuyVolume"])
        sell_volume = float(data["totalSellVolume"])
        timestamp = data["time"]
        
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
        holders = json.dumps(data)
        timestamp = data["timestamp"] / 1000  # Convert to seconds
        top_ownership_percentage = data["topOwnershipPercentage"]

        
        # Call the holder insertion procedure
        DB.call_procedure("insert_token_holders", ["TEXT","JSONB", "NUMERIC","DOUBLE PRECISION"],public_key, holders, top_ownership_percentage, timestamp)
        
    except Exception as e:
        logging.error(f"Error in storing top holders: {e}")
        raise
