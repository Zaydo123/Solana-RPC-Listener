from handlers import store_token, store_price, store_volume, store_top_holders
import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")

"""

	Event Dispatcher

"""

async def pub_to_timescale(topic: str, data: dict):
    error_message = None
    # event types: prices, volumes, top_holders, burns, tokens
    if topic == "prices":
        try:
            await store_price(data)
        except Exception as e:
            error_message = f"Failed to store price: {e}"
    elif topic == "volumes":
        try:
            await store_volume(data)
        except Exception as e:
            error_message = f"Failed to store volume: {e}"
    elif topic == "top_holders":
        try:
            await store_top_holders(data)
        except Exception as e:
            error_message = f"Failed to store top holders: {e}"
    elif topic == "tokens":
        try:
            await store_token(data)
        except Exception as e:
            error_message = f"Failed to store tokens: {e}"
    else:
        logging.info("No handler for this topic")
        error_message = "No handler for this topic"
    if error_message:
        logging.error(error_message)
        return False
    
    return True
