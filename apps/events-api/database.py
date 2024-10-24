from dotenv import find_dotenv, load_dotenv
import psycopg
import time
import logging
import os
load_dotenv(find_dotenv(".env"))

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")

class Database: 

    def __init__(self, host, port, db, username, password, schema="public",ssl="disable"):
        self.host = host
        self.port = port
        self.sslmode = ssl
        self.username = username
        self.password = password
        self.db = db
        self.schema = schema
        self.conn = self.connect()

    def conn_still_alive(self):
        try:
            with self.conn.cursor() as cursor:
                # Checking connection status
                cursor.execute("SELECT 1")
                # Fetch and log current user and database
                cursor.execute("SELECT current_user")
                current_user = cursor.fetchone()[0]  # Fetch the first result
                cursor.execute("SELECT current_database()")
                current_db = cursor.fetchone()[0]
                logging.info(f"Connected to database: {current_db} as {current_user}")
                return True
        except psycopg.OperationalError as e:
            logging.error(f"Connection check failed: {e}")
            return False
        
        
    def connect(self):
        logging.info(f"Connecting to database: {self.host}:{self.port}")
        CONN_STRING = f"host={self.host} port={self.port} dbname={self.db} user={self.username} password={self.password} sslmode={self.sslmode} options='-c search_path={self.schema}'"
        self.conn = psycopg.connect(CONN_STRING)
        return self.conn

    def execute_script(self, script, *args):
        logging.debug(f"Executing script: {script}")
        with open(f"./sql/{script}.SQL", "r") as f:
            query = f.read()
            logging.debug(f"Executing script: {script}")
            with self.conn.cursor() as cursor:
                result = cursor.execute(str(query), args)
                logging.debug(f"Result: {result.statusmessage}")
            self.conn.commit()
        return result


    def execute_query(self, query):
        with self.conn.cursor() as cursor:
            result = cursor.execute(query)
        self.conn.commit()
        return result
    
    def call_procedure(self, procedure, *args, retries=3):
        # Construct the SQL CALL statement with explicit type casting for TEXT and TIMESTAMPTZ
        query_parts = []
        for i, arg in enumerate(args):
            if isinstance(arg, str):  # Cast strings to TEXT
                query_parts.append("CAST(%s AS TEXT)")
            else:
                # do not cast for other types
                query_parts.append("%s")
                

        query = f"CALL {procedure}({', '.join(query_parts)})"
        
        attempt = 0
        while attempt < retries:
            try:
                with self.conn.cursor() as cursor:
                    logging.debug(f"Calling procedure: {query} with args: {args}")
                    cursor.execute(query, args)
                    self.conn.commit()  # Commit the transaction if successful
                    logging.info(f"Procedure {procedure} executed successfully")
                    return  # Exit if successful
            except Exception as e:
                self.conn.rollback()  # Rollback the transaction in case of error
                logging.error(f"Error calling procedure {procedure}: {e}")
                attempt += 1
                if attempt < retries:
                    logging.info(f"Retrying... attempt {attempt + 1}/{retries}")
                    time.sleep(1)  # Optional: Wait 1 second before retrying
                else:
                    raise

    
    def create_tables(self):
        return self.execute_script("CREATE_TABLES")

    def create_insertion_procedures(self):
        return self.execute_script("CREATE_INSERTION_PROCEDURES")

    def close(self):
        self.conn.close()


