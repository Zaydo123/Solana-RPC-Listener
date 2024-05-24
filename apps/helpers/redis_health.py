from colorama import Fore, Back, init
from time import sleep
import logging

init(autoreset=True)

class HealthTask:
    def __init__(self, redis_client, interval, emergency_callback):
        self.redis_client = redis_client
        self.interval = interval
        self.emergency_callback = emergency_callback

    def run(self):
            while True:
                try:
                    sleep(self.interval)
                    logging.info("♥ Healthy ♥")
                    self.redis_client.ping()
                except Exception as e:
                    logging.fatal(f"{Fore.RED}Redis health check failed: {e}")
                    self.emergency_callback()
                