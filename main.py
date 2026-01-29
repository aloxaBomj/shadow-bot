import asyncio
import json
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Настройки
TOKEN = "8515075810:AAEzB-TtZSWqGyGq-qMNEXnwCZa1WTBPtsI"  # Замени это
ADMIN_ID = 6983785240  # Замени на свой Telegram ID (узнать у @userinfobot)

logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояния для диалога
class OrderForm(StatesGroup):
    name = State()
    service = State()
    description = State()
    contact = State()
    confirm = State()

# Клавиатуры
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎯 Оставить заявку")],
        [KeyboardButton(text="📋 Прайс-лист"), KeyboardButton(text="☎️ Контакты")]
    ],
    resize_keyboard=True
)

services_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌐 Разработка программ")],
        [KeyboardButton(text="🏢 Аудит инфраструктуры")],
        [KeyboardButton(text="🔍 OSINT расследование")],
        [KeyboardButton(text="🎓 Обучение персонала")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True
)

confirm_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Подтвердить")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True
)

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    welcome_text = """
👁️ Добро пожаловать в SHADOW_SEC
    
Я принимаю заявки на аудит безопасности.
Все данные конфиденциальны и удаляются после обработки.

Выберите действие:
    """
    await message.answer(welcome_text, reply_markup=main_kb)

# Начало заявки
@dp.message(F.text == "🎯 Оставить заявку")
async def start_order(message: Message, state: FSMContext):
    await state.set_state(OrderForm.name)
    await message.answer(
        "🔒 Режим конфиденциальной связи активирован\n\n"
        "Введите ваш псевдоним или название компании:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
    )

# Отмена
@dp.message(F.text == "❌ Отмена")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Операция отменена", reply_markup=main_kb)

# Получение имени
@dp.message(OrderForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(OrderForm.service)
    await message.answer("Выберите тип услуги:", reply_markup=services_kb)

# Получение услуги
@dp.message(OrderForm.service)
async def process_service(message: Message, state: FSMContext):
    await state.update_data(service=message.text)
    await state.set_state(OrderForm.description)
    await message.answer(
        "Опишите задачу или ситуацию:\n"
        "(что нужно сделать, объем работ, сроки)",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
    )

# Получение описания
@dp.message(OrderForm.description)
async def process_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(OrderForm.contact)
    await message.answer(
        "Укажите способ связи:\n"
        "(Telegram @username, почта или номер телефона)",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
    )

# Получение контакта и подтверждение
@dp.message(OrderForm.contact)
async def process_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()
    
    preview = f"""
📩 *НОВАЯ ЗАЯВКА*

👤 Имя: {data['name']}
🎯 Услуга: {data['service']}
📝 Описание: {data['description']}
📞 Контакт: {data['contact']}

Все верно?
    """
    await state.set_state(OrderForm.confirm)
    await message.answer(preview, reply_markup=confirm_kb, parse_mode="Markdown")

# Подтверждение
@dp.message(F.text == "✅ Подтвердить", OrderForm.confirm)
async def confirm_order(message: Message, state: FSMContext):
    data = await state.get_data()
    
    # Логирование в файл
    order_data = {
        "date": datetime.now().isoformat(),
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        **data
    }
    
    with open("orders.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(order_data, ensure_ascii=False) + "\n")
    
    # Отправка админу
    admin_msg = f"""
🚨 *НОВАЯ ЗАЯВКА С САЙТА*

👤 Клиент: {data['name']}
🎯 Услуга: {data['service']}
📝 Задача: {data['description']}
📞 Связь: {data['contact']}
🔗 Telegram: @{message.from_user.username or 'N/A'}

⏰ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    
    try:
        await bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Не удалось отправить админу: {e}")
    
    await message.answer(
        "✅ Заявка принята и отправлена на обработку.\n\n"
        "Свяжусь с вами в течение 24 часов в порядке очереди.\n"
        "Удалите переписку после сохранения контакта, если требуется.",
        reply_markup=main_kb
    )
    await state.clear()

# Прайс
@dp.message(F.text == "📋 Прайс-лист")
async def price_list(message: Message):
    text = """
💰 *АКТУАЛЬНЫЕ ТАРИФЫ*

🌐 Разработка любой сложности — от 15 000₽
🏢 Аудит инфраструктуры — от 80 000₽  
🔍 OSINT расследование — от 5 000₽
🎓 Обучение (группа) — от 15 000₽/чел

*Точная стоимость определяется после анализа ТЗ*
    """
    await message.answer(text, parse_mode="Markdown")

# Контакты
@dp.message(F.text == "☎️ Контакты")
async def contacts(message: Message):
    await message.answer(
        "Каналы связи:\n\n"
        "🤖 Этот бот (оперативно)\n"
        "📧 secure@protonmail.com\n"
        "🔐 PGP: запросите в личных сообщениях",
        reply_markup=main_kb
    )

# Обработка ошибок
@dp.message()
async def echo(message: Message):
    await message.answer("Используйте кнопки меню или /start", reply_markup=main_kb)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())