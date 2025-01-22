from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Profile
from aiogram.filters.state import StateFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile

from config import logger
from utils import calc_water_intake, open_weather_api, open_food_fact_api, calc_calories_intake, calc_workout, plot_water_chart, plot_calories_chart


# Роутер обработчиков воды, еды и калорий.
router = Router()

# Хранилища данных пользователей
users = {}


# Клавиатура для выбора типа активности.
activity_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Бег", callback_data="activity:run")],
        [InlineKeyboardButton(text="Йога", callback_data="activity:yoga")],
        [InlineKeyboardButton(text="Плавание", callback_data="activity:swimming")],
        [InlineKeyboardButton(text="Силовая", callback_data="activity:strength")]
    ],
    row_width=2
)


@router.message(Command('start'))
async def send_welcome(message: types.Message):
    """Приветственное сообщение."""

    logger.info(f"/start: пользователь {message.from_user.id} запустил бота.")
    await message.reply(
        "\U0001F44B Привет! Я бот, помогающий отслеживать ваш профиль.\n"
        "Используйте /set_profile для настройки профиля.\n"
        "Описания команд можете увидеть с помощью /help."
    )


@router.message(Command('help'))
async def show_help(message: types.Message):
    """Вспомогательная команда."""

    logger.info(f"/help: пользователь {message.from_user.id} вызвал помощь.")
    await message.reply(
        "\U0001F441 Бот предоставляет следующие команды:\n\n"
        "1) */set_profile* - настройка профиля, без параметров.\n"
        "Числовые характеристики должны быть положительными, возраст и минуты активности - целыми.\n"
        "Для выбора пола нужно отправить 'м' (мужской) или 'ж' (женский).\n"
        "Команда также подходит для изменения профиля.\n\n"
        "2) */log_water <water_ml>* - логирование выпитой воды.\n"
        "Количество мл воды water\\_ml должно быть положительным."
        "Указывать количество воды обязательно.\n\n"
        "3) */log_food <product_name>, <product_g>* - логирование потребленных калорий.\n" 
        "Указывать продукт product\\_name обязательно, указывать граммовку product\\_g не обязательно.\n"
        "В случае указания граммовки укажите положительное число через запятую.\n"
        "В случае пропуска параметра граммовки вес будет считаться как 100 г.\n\n"
        "4) */log_workout <type> <time>* - логирование тренировки.\n" 
        "Оба параметра обязательно и разделяются пробелом.\n"
        "Доступные типы тренировок type: бег, йога, плавание, силовая (любой регистр).\n"
        "В качестве времени тренировки time укажите целое положительное число минут.\n\n"
        "5) */check_progress* - текущий прогресс, без параметров.\n" 
        "Команда приводит текущие результаты по потреблению воды и калориям.\n"
        "Предоставляются графики прогресса.\n\n"
        "6) */new_day* - обновление трекинга, без параметров.\n" 
        "Команда обнуляет текущйи прогресс, приводят его итоговые результаты.\n"
        "Отсчет по воде и калориям начинается заново, происходит перерасчет нормы воды.\n\n"
        "7) */profile_info* - информация профиля, без параметров.\n" 
        "Команда выводит текущие данные профиля.\n\n"
        "\U0001F6D1 ВАЖНО:\n"
        "- разделителем для чисел с плавающей точкой является точка '.';\n"
        "- перед выполнением команд логирования / прогресса заполните профиль!",
        parse_mode="Markdown"
    )


@router.message(Command('set_profile'))
async def set_profile(message: types.Message, state: FSMContext):
    """Начало настройки профиля."""

    user_id = message.from_user.id
    logger.info(f"/set_profile: пользователь {user_id} начал настройку профиля.")
    users[user_id] = {
        "weight": None,
        "height": None,
        "age": None,
        "gender": None,
        "activity": None,
        "activity_type": None,
        "city": None,
        "water_goal": None,
        "calorie_goal": None,
        "logged_water": 0,
        "logged_calories": 0,
        "burned_calories": 0
    }

    await state.set_state(Profile.weight)
    await message.reply("Введите ваш вес в килограммах:")


@router.message(Profile.weight)
async def process_weight(message: types.Message, state: FSMContext):
    """Обработка введенного веса."""

    try:
        weight = float(message.text)
        if weight <= 0:
            raise ValueError("Вес должен быть положительным числом.")
        user_id = message.from_user.id
        users[user_id]['weight'] = weight

        await state.update_data(weight=weight)
        logger.info(f"/set_profile: пользователь {user_id} ввел вес.")
        await state.set_state(Profile.height)
        await message.reply("Введите ваш рост в см:")
    except ValueError as e:
        logger.error(f"/set_profile, ошибка ввода веса: {e}")
        await message.reply("Пожалуйста, введите положительное число.")


@router.message(Profile.height)
async def process_height(message: types.Message, state: FSMContext):
    """Обработка введенного роста."""

    try:
        height = float(message.text)
        if height <= 0:
            raise ValueError("Рост должен быть положительным числом.")
        user_id = message.from_user.id
        users[user_id]['height'] = height

        await state.update_data(height=height)
        logger.info(f"/set_profile: пользователь {user_id} ввел рост.")
        await state.set_state(Profile.age)
        await message.reply("Введите ваш возраст в годах:")
    except ValueError as e:
        logger.error(f"/set_profile, ошибка ввода роста: {e}")
        await message.reply("Пожалуйста, введите положительное число.")


@router.message(Profile.age)
async def process_age(message: types.Message, state: FSMContext):
    """Обработка введенного возраста."""

    try:
        age = int(message.text)
        if age < 14 or age > 100:
            raise ValueError("Количество лет невалидно.")
        user_id = message.from_user.id
        users[user_id]['age'] = age

        await state.update_data(age=age)
        logger.info(f"/set_profile: пользователь {user_id} ввел возраст.")
        await state.set_state(Profile.gender)
        await message.reply("Укажите Ваш пол - мужской (м) или женский (ж):")
    except ValueError as e:
        logger.error(f"/set_profile, ошибка ввода возраста: {e}")
        await message.reply("Пожалуйста, введите полное количество лет (от 14 до 100).")


@router.message(Profile.gender)
async def process_gender(message: types.Message, state: FSMContext):
    """Обработка введенного пола."""

    try:
        gender = message.text.lower()
        if gender not in ['м', 'ж']:
            raise ValueError("Введено невалидное значение для пола.")
        user_id = message.from_user.id
        users[user_id]['gender'] = gender

        await state.update_data(gender=gender)
        logger.info(f"/set_profile: пользователь {user_id} ввел пол.")
        await state.set_state(Profile.activity)
        await message.reply("Введите Ваш уровень активности в минутах в день:")
    except ValueError as e:
        logger.error(f"/set_profile, ошибка ввода пола: {e}")
        await message.reply("Пожалуйста, введите пол в формате 'м' или 'ж'.")


@router.message(Profile.activity)
async def process_activity(message: types.Message, state: FSMContext):
    """Обработка введенного уровня активности в минутах."""

    try:
        activity_minutes = int(message.text)
        if activity_minutes <= 0 or activity_minutes > 1440:
            raise ValueError("Количество минут невалидно.")
        user_id = message.from_user.id
        users[user_id]['activity'] = activity_minutes

        await state.update_data(activity=activity_minutes)
        logger.info(f"/set_profile: пользователь {user_id} ввел дневную активность.")
        await state.set_state(Profile.activity_type)
        await message.reply(f"Выберите наиболее подходящий тип активности:", reply_markup=activity_keyboard)
    except ValueError as e:
        logger.error(f"/set_profile, ошибка ввода активности: {e}")
        await message.reply("Пожалуйста, введите целое валидное значение минут в день (от 1 до 1440).")


@router.callback_query(StateFilter(Profile.activity_type), lambda c: c.data.startswith("activity:"))
async def process_activity_type(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа активности."""

    activity_type_mapping = {
        "activity:run": "Бег",
        "activity:yoga": "Йога",
        "activity:swimming": "Плавание",
        "activity:strength": "Силовая"
    }

    try:
        activity_type = activity_type_mapping.get(callback_query.data)
        
        if not activity_type:
            logger.error(f"/set_profile, ошибка выбора типа активности.")
            await callback_query.answer("Неверный выбор, попробуйте снова:", show_alert=True)
            return
        
        user_id = callback_query.from_user.id
        users[user_id]['activity_type'] = activity_type

        await state.update_data(activity_type=activity_type)
        logger.info(f"/set_profile: пользователь {user_id} выбрал тип активности.")
        await state.set_state(Profile.city)
        await callback_query.message.answer(
            f"Вы выбрали {activity_type}.\n"
            "Введите ваш город для получения температуры:"
        )
        await callback_query.answer()
    except Exception as e:
        logger.error(f"/set_profile, ошибка выбора типа активности: {e}")
        await callback_query.message.answer("Возникли проблемы в работе бота, попробуйте позже.")


@router.message(Profile.city)
async def process_city(message: types.Message, state: FSMContext):
    """Обработка введенного города."""
    
    try:
        city = message.text.title()
        if city == '+':
            city = 'Москва'
        user_id = message.from_user.id
        users[user_id]['city'] = city

        await state.update_data(city=city)

        # Извлекаем данные состояния.
        data = await state.get_data()
        weight = data.get('weight')
        activity = data.get('activity')
        # Расчет температуры и нормы воды.
        temperature =  await open_weather_api(city) if city else 20
        water_goal = calc_water_intake(weight, activity, temperature)
        users[user_id]['water_goal'] = water_goal
        logger.info(f"/set_profile: пользователь {user_id} ввел город. Рассчитана дневная норма воды.")

        await state.set_state(Profile.calorie_goal)
        await message.reply(
            f"На текущий момент в городе {city} {temperature} градусов Цельсия.\n"
            "Введите вашу дневную цель калорий (или отправьте '-' для автоматического расчета):"
        )
    except ValueError as e:
        logger.error(f"/set_profile, ошибка ввода города: {e}")
        await message.reply(
            "Введен невалидный город, попробуйте снова.\n"
            "Если Вы уверены, что верно ввели название города - отправьте '+'. "
            "В таком случае будет присвоен город по умолчанию - Москва."
        )


@router.message(Profile.calorie_goal)
async def process_calorie_goal(message: types.Message, state: FSMContext):
    """Обработка цели калорий."""

    calorie_goal_str = message.text.strip()
    data = await state.get_data()
    weight = data['weight']
    height = data['height']
    age = data['age']
    gender = data['gender']
    activity = data['activity']
    activity_type = data['activity_type']

    # Автоматический расчет нормы калорий.
    if calorie_goal_str == '-':
        calorie_goal = calc_calories_intake(weight, height, gender, age, activity, activity_type)
    # Введенная пользователем цель.
    else:
        try:
            calorie_goal = float(calorie_goal_str)
            if calorie_goal < 0:
                raise ValueError("Количесвто калорий не может быть отрицательным числом.")
        except ValueError as e:
            logger.error(f"/set_profile, ошибка ввода цели по калориям: {e}")
            await message.reply("Введено невалидное значение для калорий, пожалуйста, повторите.")
            return

    user_id = message.from_user.id
    users[user_id]['calorie_goal'] = calorie_goal
    await state.update_data(calorie_goal=calorie_goal)
    logger.info(f"/set_profile: пользователь {user_id} ввел цель по калориям.")

    city = data['city']
    water_goal = users[user_id]['water_goal']

    # Ответ с заполненным профилем пользователя
    summary = (
        f"\U0001F4CE Ваш профиль:\n"
        f"Вес: {weight} кг\n"
        f"Рост: {height} см\n"
        f"Возраст: {age} лет\n"
        f"Пол: {'женский' if gender == 'ж' else 'мужской'},\n"
        f"Уровень активности: {activity} минут в день,\n"
        f"Предпочтительный тип активности: {activity_type},\n"
        f"Город: {city},\n"
        f"Норма воды: {water_goal},\n"
        f"Цель калорий: {calorie_goal} ккал."
    )
    await message.reply(summary)
    await state.clear()


@router.message(Command('log_water'))
async def log_water(message: types.Message):
    """Обработка команды логирования воды."""

    user_id = message.from_user.id
    logger.info(f"/log_water: пользователь {user_id} вызвал логирование воды.")
    if user_id not in users:
        logger.warning(f"/log_water: пользователь {user_id} еще не настроил профиль.")
        await message.answer("Пожалуйста, настройте профиль с помощью команды /set_profile.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        logger.warning(f"/log_water: пользователь {user_id} не указал параметры.")
        await message.reply("Пожалуйста, укажите кол-во воды в мл. Например: /log_water 200")
        return
    
    try:
        amount = float(args[1])
        if amount <= 0:
            raise ValueError("Количество должно быть положительным числом.")

        # Обновление логов воды
        users[user_id]['logged_water'] += amount
        # Остаток до дневной нормы
        remains = max(0, users[user_id]['water_goal'] - users[user_id]['logged_water'])

        await message.reply(
            f"\U0001F4A7 Вы выпили {amount} мл воды;\n"
            f"Всего за день выпито: {users[user_id]['logged_water']} мл;\n"
            f"Осталось до выполнения дневной нормы: {remains:.2f} мл."
        )
    except ValueError as e:
        logger.error(f"/log_water, ошибка логирования воды: {e}")
        await message.reply("Пожалуйста, укажите количество воды в виде одного положительного числа.")


@router.message(Command('log_food'))
async def log_water(message: types.Message):
    """Обработка команды логирования еды."""

    user_id = message.from_user.id
    logger.info(f"/log_food: пользователь {user_id} вызвал логирование еды.")
    if user_id not in users:
        logger.warning(f"/log_food: пользователь {user_id} еще не настроил профиль.")
        await message.answer("Пожалуйста, настройте профиль с помощью команды /set_profile.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        logger.warning(f"/log_food: пользователь {user_id} не указал параметры.")
        await message.reply(
            "Пожалуйста, укажите продукт и граммовку через запятую при необходимости. "
            "Например: /log_food банан, 120"
        )
        return
    
    try:
        product_data = args[1].rsplit(sep=', ', maxsplit=1)
        product_name = product_data[0].lower()

        # Указана ли граммовка
        if len(product_data) == 1:
            product_weight = 100.0
        else:
            product_weight = float(product_data[1])
            if product_weight <= 0:
                raise ValueError("Граммовка должна быть положительным числом.")
        
        # Количество калорий через API.
        calories = await open_food_fact_api(product_name, product_weight)
        users[user_id]['logged_calories'] += calories

        await message.reply(
            f"\U0001F355 Продукт: {product_name}, вес: {product_weight} г, калорий: {calories:.2f};\n"
            f"Всего потреблено за день: {users[user_id]['logged_calories']:.2f} ккал."
        )

    except (IndexError, ValueError) as e:
        logger.error(f"/log_food, ошибка логирования еды: {e}")
        await message.reply("Указаны невалидные параметры для команды, обратитесь к помощи /help.")


@router.message(Command('log_workout'))
async def log_workout(message: types.Message):
    """Обработка команды логирования тренировки."""

    user_id = message.from_user.id
    logger.info(f"/log_workout: пользователь {user_id} вызвал логирование тренировки.")
    if user_id not in users:
        logger.warning(f"/log_workout: пользователь {user_id} еще не настроил профиль.")
        await message.answer("Пожалуйста, настройте профиль с помощью команды /set_profile.")
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        logger.warning(f"/log_workout: пользователь {user_id} не указал параметры.")
        await message.reply("Пожалуйста, укажите тип тренировки и время (в минутах). Например: /log_workout бег 30")
        return

    try:
        workout_type = args[1].lower()
        workout_time = int(args[2])

        if workout_time <= 0:
            raise ValueError("Время должно быть положительным целым числом минут.")
        
        if workout_type not in ['бег', 'йога', 'плавание', 'силовая']:
            logger.warning(f"/log_workout: пользователь {user_id} указал невалидный тип активности.")
            await message.reply("Неизвестный тип тренировки. Доступные варианты: бег, йога, плавание, силовая.")
            return

        # Расчет калорий и воды.
        calories, water_opt = calc_workout(workout_type, workout_time)

        # Логируем данные о сожженных калориях. 
        users[user_id]['burned_calories'] += calories
        users[user_id]['water_goal'] += water_opt

        await message.reply(
            f"\U0001F3CB {workout_type.capitalize()} {workout_time} минут — сожжено {calories} ккал.\n"
            f"Дневная норма воды с учетом тренировки: {users[user_id]['water_goal']},\n"
            f"Дополнительно выпейте {water_opt} мл воды."
        )

    except (IndexError, ValueError) as e:
        logger.error(f"/log_workout, ошибка логирования тренировки: {e}")
        await message.reply("Указаны невалидные параметры для команды, обратитесь к помощи /help.")


@router.message(Command("check_progress"))
async def check_progress(message: types.Message):
    """Обработка команды вывода прогресса."""

    user_id = message.from_user.id
    logger.info(f"/check_progress: пользователь {user_id} просматривает прогресс.")
    if user_id not in users:
        logger.warning(f"/check_progress: пользователь {user_id} еще не настроил профиль.")
        await message.reply("Пожалуйста, сначала настройте профиль через команду /set_profile.")
        return 
    
    user_data = users[user_id]
    
    try:
        # Данные по воде.
        water_log = user_data['logged_water']
        water_goal = user_data['water_goal']
        water_remain = max(0, water_goal - water_log)
        water_chart = plot_water_chart(water_log, water_remain)
        water_file = BufferedInputFile(water_chart.getvalue(), filename="water_progress.png")

        # Данные по калориям.
        calorie_goal = user_data['calorie_goal']
        calorie_log = user_data['logged_calories']
        calorie_burned = user_data['burned_calories']
        calorie_balance = calorie_log - calorie_burned
        calorie_chart = plot_calories_chart(calorie_goal, calorie_log, calorie_burned)
        calorie_file = BufferedInputFile(calorie_chart.getvalue(), filename="calorie_progress.png")

        await message.reply(
            f"\U0001F4CA Ваш текущий прогресс:\n"
            f"\U0001F4A7 Вода:\n"
            f"- Выпито: {water_log} из {water_goal} мл,\n"
            f"- Осталось: {water_remain} мл;\n\n"
            f"\U0001F355 Калории:\n"
            f"- Потреблено: {calorie_log} ккал из {calorie_goal} ккал,\n"
            f"- Сожжено: {calorie_burned} ккал,\n"
            f"- Баланс: {calorie_balance}."
        )

        await message.answer_photo(photo=water_file, caption="Прогресс потребления воды")
        await message.answer_photo(photo=calorie_file, caption="Прогресс по калориям")
    except Exception as e:
        logger.error(f"/check_progress, ошибка просмотра прогресса: {e}")
        await message.reply("Возникли проблемы в работе бота, попробуйте позже.")


@router.message(Command("new_day"))
async def fix_new_day(message: types.Message):
    """Обработка команды фиксирования нового дня."""
    
    user_id = message.from_user.id
    logger.info(f"/new_day: пользователь {user_id} вызвал обнуление текущего дня.")
    if user_id not in users:
        logger.warning(f"/new_day: пользователь {user_id} еще не настроил профиль.")
        await message.reply("Пожалуйста, сначала настройте профиль через команду /set_profile.")
        return
    
    try:
        # Предыдущие значения.
        user_data = users[user_id]
        
        water_log = user_data['logged_water']
        water_goal = user_data['water_goal']
        water_remain = max(0, water_goal - water_log)
        if water_remain == 0:
            water_str = f"Дневная норма воды в {water_goal} мл выполнена,\n"
        else:
            water_str = f"Дневная норма воды не выполнена, недобор в {water_remain} мл,\n"

        calorie_log = user_data['logged_calories']
        calorie_burned = user_data['burned_calories']
        calorie_balance = calorie_log - calorie_burned
        if calorie_balance > 0:
            cal_str = f"Баланс калорий положительный ({calorie_balance} ккал), ожидаем набор веса."
        elif calorie_balance < 0:
            cal_str = f"Баланс калорий отрицательный ({calorie_balance} ккал), ожидаема потеря веса."
        else:
            cal_str = f"Нейтральный баланс калорий, ожидаем стабильный вес."

        prev_day_stat = f"\U0001F519 Статистика за предыдущий день:\n" + water_str + cal_str
        
        await message.reply(prev_day_stat)

        # Обнуление логов по воде и калориям.
        users[user_id]['logged_water'] = 0
        users[user_id]['logged_calories'] = 0
        users[user_id]['burned_calories'] = 0

        # Пересчет нормы воды.
        city = users[user_id]['city']
        weight = users[user_id]['weight']
        activity = users[user_id]['activity']
        temperature =  await open_weather_api(city) if city else 20
        water_goal = calc_water_intake(weight, activity, temperature)

        await message.answer(
            f"\U0001F51C Прогресс на новый день успешно сброшен!\n"
            f"Текущая норма воды для города {city} ({temperature}) - {water_goal} мл в день.\n"
        )
    except Exception as e:
        logger.error(f"/new_day, ошибка сброса предыдущего дня: {e}")
        await message.reply("Возникли проблемы в работе бота, попробуйте позже.")


@router.message(Command("profile_info"))
async def get_profile_info(message: types.Message):
    """Обработка запроса получения информации о профиле."""

    user_id = message.from_user.id
    logger.info(f"/profile_info: пользователь {user_id} просматривает профиль.")
    if user_id not in users:
        logger.warning(f"/profile_info: пользователь {user_id} еще не настроил профиль.")
        await message.reply("Пожалуйста, сначала настройте профиль через команду /set_profile.")
        return
 
    user_data = users[user_id]
    await message.reply(
        f"\U0001F4CC Текущая информация в Вашем профиле:\n"
        f"Вес: {user_data['weight']} кг,\n"
        f"Рост: {user_data['height']} см,\n"
        f"Возраст: {user_data['age']} лет,\n"
        f"Пол: {'женский' if user_data['gender'] == 'ж' else 'мужской'},\n"
        f"Активность: {user_data['activity']} минут в день,\n"
        f"Тип активности: {user_data['activity_type']},\n"
        f"Город: {user_data['city']},\n"
        f"Норма воды: {user_data['water_goal']} мл в день,\n"
        f"Цель калорий: {user_data['calorie_goal']} ккал в день."
    )
