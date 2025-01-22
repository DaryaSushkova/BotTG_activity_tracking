import os
from dotenv import load_dotenv
import logging


# Настройка логирования.
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# Настройка логов aiogram.
logging.getLogger("aiogram.event").setLevel(logging.WARNING)
# Пользовательский логгер.
logger = logging.getLogger("bot_logger")
logger.setLevel(logging.INFO)

# Загрузка переменных из .env файла
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TG_TOKEN")
OPEN_WEATHER_KEY = os.getenv("OW_API_KEY")
OPEN_WEATHER_URL = 'http://api.openweathermap.org/data/2.5/weather'
OPEN_FOOD_FACT_URL = 'https://world.openfoodfacts.org/cgi/search.pl'

if not BOT_TOKEN or not OPEN_WEATHER_KEY:
    raise NameError