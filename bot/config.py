import os
from dotenv import load_dotenv
import logging


# Логирование при отладке
logging.basicConfig(level=logging.DEBUG)
aiohttp_logger = logging.getLogger("aiohttp")
aiohttp_logger.setLevel(logging.DEBUG)

# Загрузка переменных из .env файла
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TG_TOKEN")
OPEN_WEATHER_KEY = os.getenv("OW_API_KEY")
OPEN_WEATHER_URL = 'http://api.openweathermap.org/data/2.5/weather'
OPEN_FOOD_FACT_URL = 'https://world.openfoodfacts.org/cgi/search.pl'

if not BOT_TOKEN or not OPEN_WEATHER_KEY:
    raise NameError