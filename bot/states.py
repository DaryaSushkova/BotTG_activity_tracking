from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage


class Profile(StatesGroup):
    '''
    Состояние заполнения профиля.
    '''
    weight = State()
    height = State()
    age = State()
    activity = State()
    activity_type = State()
    city = State()
    calorie_goal = State()