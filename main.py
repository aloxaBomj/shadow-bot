import os
import json
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Настройки из переменных окружения
TOKEN = os.getenv("8515075810:AAEzB-TtZSWqGyGq-qMNEXnwCZa1WTBPtsI")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6983785240"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN or not ADMIN_ID:
    raise ValueError("Задай BOT_TOKEN и ADMIN_ID в Environment Variables!")

logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ================== СОСТОЯНИЯ ==================
class OrderForm(StatesGroup):
    name = State()
    service = State()
    description = State()
    contact = State()
    confirm = State()

# ================== КЛАВИАТУРЫ ==================
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

# ================== ОБРАБОТЧИКИ ==================
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👁️ Добро пожаловать в SHADOW_SEC\n\n"
        "Я принимаю заявки на аудит безопасности.\n"
        "Все данные конфиденциальны.\n\n"
        "Выберите действие:",
        reply_markup=main_kb
    )

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

@dp.message(F.text == "❌ Отмена")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Операция отменена", reply_markup=main_kb)

@dp.message(OrderForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(OrderForm.service)
    await message.answer("Выберите тип услуги:", reply_markup=services_kb)

@dp.message(OrderForm.service)
async def process_service(message: Message, state: FSMContext):
    await state.update_data(service=message.text)
    await state.set_state(OrderForm.description)
    await message.answer(
        "Опишите задачу подробнее (объем, сроки):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
    )

@dp.message(OrderForm.description)
async def process_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(OrderForm.contact)
    await message.answer(
        "Укажите способ связи (Telegram @username, почта или телефон):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
    )

@dp.message(OrderForm.contact)
async def process_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()
    
    preview = f"""
📩 *ПРОВЕРЬТЕ ДАННЫЕ*

👤 Имя: `{data['name']}`
🎯 Услуга: {data['service']}
📝 Задача: {data['description']}
📞 Контакт: `{data['contact']}`

Все верно?
    """
    await state.set_state(OrderForm.confirm)
    await message.answer(preview, parse_mode="Markdown", reply_markup=confirm_kb)

@dp.message(F.text == "✅ Подтвердить", OrderForm.confirm)
async def confirm_order(message: Message, state: FSMContext):
    data = await state.get_data()
    
    # Сохраняем в лог
    order_data = {
        "date": datetime.now().isoformat(),
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        **data
    }
    with open("orders.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(order_data, ensure_ascii=False) + "\n")
    
    # Отправляем админу
    admin_msg = f"""
🚨 *НОВАЯ ЗАЯВКА С САЙТА*

👤 Клиент: {data['name']}
🎯 Услуга: {data['service']}
📝 Задача: {data['description']}
📞 Связь: {data['contact']}
🔗 Telegram: @{message.from_user.username or 'нет'}

⏰ {datetime.now().strftime("%Y-%m-%d %H:%M")}
    """
    try:
        await bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Ошибка отправки админу: {e}")
    
    await message.answer(
        "✅ Заявка принята! Свяжусь в течение 24 часов.",
        reply_markup=main_kb
    )
    await state.clear()

@dp.message(F.text == "📋 Прайс-лист")
async def price_list(message: Message):
    text = """
💰 *ТАРИФЫ*

🌐 Разработка любой сложности — от 15 000₽
🏢 Аудит инфраструктуры — от 80 000₽  
🔍 OSINT расследование — от 5 000₽
🎓 Обучение (группа) — от 15 000₽/чел
    """
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "☎️ Контакты")
async def contacts(message: Message):
    await message.answer(
        "Каналы связи:\n\n"
        "🤖 Этот бот\n"
        "📧 secure@protonmail.com",
        reply_markup=main_kb
    )

@dp.message()
async def echo(message: Message):
    await message.answer("Используйте кнопки меню", reply_markup=main_kb)

# ================== WEB SERVER (FASTAPI) ==================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """При старте устанавливаем webhook"""
    if WEBHOOK_URL:
        await bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook",
            allowed_updates=types.AllowedUpdates.all()
        )
        logging.info(f"Webhook установлен: {WEBHOOK_URL}/webhook")
    yield
    await bot.delete_webhook()
    await bot.session.close()

# ⬇️ ВОТ ЭТА СТРОКА ОБЯЗАТЕЛЬНО ДОЛЖНА БЫТЬ!
app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Обработчик сообщений от Telegram"""
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot, update)
        return Response(status_code=200)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return Response(status_code=200)  # Всегда возвращаем 200, иначе Telegram заблокирует

@app.get("/")
async def health():
    """Проверка работы"""
    return {"status": "ONLINE", "service": "SHADOW_SEC"}
