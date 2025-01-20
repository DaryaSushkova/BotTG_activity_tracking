import aiohttp
import io
import matplotlib.pyplot as plt
from config import OPEN_WEATHER_URL, OPEN_WEATHER_KEY, OPEN_FOOD_FACT_URL


async def open_weather_api(city: str):
    '''
    Получение температуры из OpenWeatherMap API.
    '''

    params = {
        'q': city,
        'appid': OPEN_WEATHER_KEY,
        'units': 'metric',
        'lang': 'ru'
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(OPEN_WEATHER_URL, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data["main"]["temp"]
            else:
                raise ValueError(f"Ошибка при получении данных о погоде: {response.status}")
            

async def open_food_fact_api(product_name: str, product_weight: float) -> float:
    '''
    Получение калорийности продукта из Edamam API.
    '''

    params = {
        "search_terms": product_name,
        "search_simple": 1,
        "action": "process", 
        "json": 1
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(OPEN_FOOD_FACT_URL, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("products"):
                    # Берем первый продукт из результата поиска
                    product = data["products"][0]
                    name = product.get("product_name", "Неизвестно")
                    nutriments = product.get("nutriments", {})
                    
                    # # Получаем калории на 100 грамм
                    calories_per_100g = nutriments.get("energy-kcal_100g", "Нет данных")
                    
                    # Рассчитываем калории на заданный вес
                    if calories_per_100g != "Нет данных":
                        calories = round(calories_per_100g * product_weight / 100, 2)
                    else:
                        calories = 0
                    
                    #return f"Продукт: {name}, Калории: {calories_per_100g} ккал"
                    return calories
                else:
                    return "Продукт не найден."
            else:
                return f"Ошибка: {response.status}"


def calc_water_intake(weight: float, activity: int, temperature: float) -> float:
    '''
    Расчет дневной нормы воды в миллилитрах.
    '''

    # Расчет с учетом базовой части, активности и температуры.
    total_water = weight * 30 + (activity // 30) * 500 + (500 if temperature > 25 else 0)
    return total_water


def calc_calories_intake(weight: float, height: float, age: int, activity: int) -> float:
    '''
    Расчет дневной нормы калорий.
    '''

    # Расчет базового обмена веществ.
    bmr = weight * 10 + 6.25 * height + age * 5
    bmr += (200 if activity <= 30 else (300 if activity <= 60 else 400))

    return bmr


def plot_water_chart(water_logged, water_remains):
    '''
    Построение и передача графика потребления воды.
    '''
    
    data = [water_logged, water_remains]
    labels = ["Выпито (мл)", "Осталось (мл)"]
    colors = ["#76c7c0", "#ffcccb"]

    plt.figure(figsize=(6, 6))
    plt.pie(data, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors)
    plt.title("Прогресс потребления воды за день")

    # Сохранение графика в байтовый объект.
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)
    return buffer


def plot_calories_chart(calories_goal, calories_logged, calories_burned):
    '''
    Построение и передача графика отслеживания калорий.
    '''

    categories = ["Потреблено", "Сожжено", "Цель"]
    values = [calories_logged, calories_burned, calories_goal]
    colors = ["#76c7c0", "#ffcccb", "#ffda79"]

    plt.figure(figsize=(8, 5))
    plt.bar(categories, values, color=colors)
    plt.title("Прогресс калорий")
    plt.ylabel("Калории (ккал)")

    # Сохранение графика в байтовый объект.
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)
    return buffer