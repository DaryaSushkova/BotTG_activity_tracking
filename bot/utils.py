import aiohttp
import io
import matplotlib.pyplot as plt
from config import OPEN_WEATHER_URL, OPEN_WEATHER_KEY, OPEN_FOOD_FACT_URL


# Соотношение типов активности и ккал/мин.
ACTIVITY_CALORIES = {
    "бег": 10,     
    "плавание": 8,  
    "силовая": 6,   
    "йога": 3   
}


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
    Получение калорийности продукта из Open Food Facts.
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
                    # Первый продукт из результата поиска.
                    product = data["products"][0]
                    nutriments = product.get("nutriments", {})
                    # Калории на 100 грамм.
                    calories_100 = nutriments.get("energy-kcal_100g", "Нет данных")
                    
                    # Калории на заданный вес.
                    if calories_100 != "Нет данных":
                        calories = round(calories_100 * product_weight / 100, 2)
                    else:
                        calories = 0.0
                    
                    return calories
                else:
                    return 0.0
            else:
                return 0.0


def calc_water_intake(weight: float, activity: int, temperature: float) -> float:
    '''
    Расчет дневной нормы воды в миллилитрах.
    '''

    # Расчет с учетом базовой части, активности и температуры.
    total_water = weight * 30 + (activity // 30) * 500 + (500 if temperature > 25 else 0)
    return total_water


def calc_calories_intake(weight: float, height: float, gender: str, age: int, activity: int, activity_type: str) -> float:
    '''
    Расчет дневной нормы калорий.
    '''
    
    # Слагаемое, зависящее от пола.
    gender_opt = 5.0 if gender == 'м' else -161.0
    # Расчет базового обмена веществ по уравнению Харриса-Бенедикта.
    bmr = weight * 10 + 6.25 * height + age * 5 + gender_opt
    # Учет активности.
    bmr += ACTIVITY_CALORIES.get(activity_type.lower(), 0) * activity

    return bmr


def calc_workout(workout_type: str, workout_time: int):
    '''
    Расчет сожженных калорий и дополнительной воды.
    '''

    calories = 0
    water_opt = 0

    # Учет разных типов тренировок.
    if workout_type == "бег":
        calories = workout_time * ACTIVITY_CALORIES.get(workout_type.lower(), 0)
        water_opt = (workout_time // 30) * 200
    elif workout_type == "йога":
        calories = workout_time * ACTIVITY_CALORIES.get(workout_type.lower(), 0)
        water_opt = (workout_time // 30) * 150
    elif workout_type == "плавание":
        calories = workout_time * ACTIVITY_CALORIES.get(workout_type.lower(), 0)
        water_opt = (workout_time // 30) * 250
    elif workout_type == "силовая":
        calories = workout_time * ACTIVITY_CALORIES.get(workout_type.lower(), 0)
        water_opt = (workout_time // 30) * 200

    return calories, water_opt


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
    plt.grid(True)

    # Сохранение графика в байтовый объект.
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)
    return buffer