from dotenv import find_dotenv, load_dotenv
import psycopg
import time
import logging

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")

class Database: 

    def __init__(self, host, port, username, password, ssl="disable"):
        self.host = host
        self.port = port
        self.sslmode = ssl
        self.username = username
        self.password = password
        self.conn = self.connect()

    def conn_still_alive(self):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        except psycopg.OperationalError:
            return False
        return True

    def connect(self):
        logging.info(f"Connecting to database: {self.host}:{self.port}")
        CONN_STRING = f"postgres://{self.username}:{self.password}@{self.host}:{self.port}"
        CONN_STRING += f"?sslmode={self.sslmode}"
        self.conn = psycopg.connect(CONN_STRING)
        return self.conn

    def execute_script(self, script):
        logging.debug(f"Executing script: {script}")
        with open(f"./sql/{script}.sql", "r") as f:
            query = f.read()
            logging.debug(f"Executing script: {script}")
            with self.conn.cursor() as cursor:
                result = cursor.execute(str(query))
                logging.debug(f"Result: {result}")
            self.conn.commit()
        return result

    def execute_query(self, query):
        with self.conn.cursor() as cursor:
            result = cursor.execute(query)
        self.conn.commit()
        return result
    
    def call_procedure(self, procedure, *args, retries=3):
        query = f"CALL {procedure}("
        query += ",".join(["%s" for _ in args]) + ")"
        logging.debug(f"Calling procedure: {query}")
        
        attempt = 0
        while attempt < retries:
            try:
                with self.conn.cursor() as cursor:
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


