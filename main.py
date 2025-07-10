import logging
import os
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiohttp import web
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 584791919

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния
class RequestForm(StatesGroup):
    name = State()
    phone = State()
    question = State()

# Клавиатура
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(
    KeyboardButton("📄 Жиі қойылатын сұрақтар"),
    KeyboardButton("📝 Өтінім қалдыру")
)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer(
        "Сәлеметсіз бе! Бұл бот бастауыш сынып мұғалімдеріне арналған әдістемелік көмек көрсету үшін жасалған.\nТөменнен қажетті бөлімді таңдаңыз:",
        reply_markup=main_kb
    )

@dp.message_handler(lambda message: message.text == "📄 Жиі қойылатын сұрақтар")
async def faq_handler(message: types.Message):
    await message.answer(
        "🤔 *Жиі қойылатын сұрақтар:*\n\n"
        "1. Сабақ жоспары бойынша сұрақтар\n"
        "2. Бағалау бойынша сұрақтар\n"
        "3. Пән бойынша сұрақтар: Математика, Қазақ тілі, Жаратылыстану, Дүниетану, Әліппе\n"
        "4. Мақала жариялау\n5. Сыныпты басқару\n6. АКТ\n7. Психологиялық тренингтер\n8. Курс бойынша сұрақтар\n9. Семинарлар\n10. Анықтама\n11. Курстан кейінгі қолдау\n12. Ашық сабақ\n13. Педагогикалық идеялар сайысы\n14. Авторлық бағдарлама\n15. Басқа да сұрақтар\n\n"
        "👩‍🏫 Сіздің өтіліңіз қанша жыл?",
        parse_mode="Markdown"
    )

@dp.message_handler(lambda message: message.text == "📝 Өтінім қалдыру")
async def start_request(message: types.Message):
    await message.answer("👤 Атыңызды жазыңыз:", reply_markup=ReplyKeyboardRemove())
    await RequestForm.name.set()

@dp.message_handler(state=RequestForm.name)
async def request_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    contact_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    contact_kb.add(KeyboardButton("📲 Нөмірімді жіберу", request_contact=True))
    contact_kb.add(KeyboardButton("✍️ Өзім жазамын"))
    await message.answer("📞 Телефон нөміріңізді жіберіңіз немесе жазыңыз:", reply_markup=contact_kb)
    await RequestForm.phone.set()

@dp.message_handler(content_types=types.ContentType.CONTACT, state=RequestForm.phone)
async def get_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("📝 Сұрағыңызды сипаттап жазыңыз:", reply_markup=ReplyKeyboardRemove())
    await RequestForm.question.set()

@dp.message_handler(lambda message: message.text.startswith("✍️"), state=RequestForm.phone)
async def ask_manual_phone(message: types.Message):
    await message.answer("📞 Телефон нөміріңізді жазыңыз:")

@dp.message_handler(state=RequestForm.phone)
async def get_manual_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("📝 Сұрағыңызды сипаттап жазыңыз:")
    await RequestForm.question.set()

@dp.message_handler(state=RequestForm.question)
async def get_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data['name']
    phone = data['phone']
    question = message.text

    text = (
        f"📅 *Жаңа өтінім!*\n"
        f"\n👤 Аты: {name}"
        f"\n📞 Телефон: {phone}"
        f"\n💬 Сұрақ: {question}"
        f"\n\n📲 WhatsApp: https://wa.me/{''.join(filter(str.isdigit, phone))}"
    )
    await bot.send_message(ADMIN_CHAT_ID, text, parse_mode="Markdown")
    await message.answer("Рақмет! Өтініміңіз жіберілді.", reply_markup=main_kb)
    await state.finish()

# Веб-сервер anti-sleep
async def web_handler(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get('/', web_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get('PORT', 8080)))
    await site.start()

async def main():
    await asyncio.gather(
        web_server(),
        dp.start_polling()
    )

if __name__ == '__main__':
    asyncio.run(main())
