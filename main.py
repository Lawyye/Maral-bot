import logging
import os
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
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

# Главное меню
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(
    KeyboardButton("📄 Жиі қойылатын сұрақтар"),
    KeyboardButton("📝 Өтінім қалдыру")
)

# === FAQ Многоуровневое меню === #
faq_main_kb = InlineKeyboardMarkup(row_width=1)
faq_main_kb.add(
    InlineKeyboardButton("📚 Пән бойынша сұрақтар", callback_data="cat_1"),
    InlineKeyboardButton("📝 Бағалау / Сабақ жоспары", callback_data="cat_2"),
    InlineKeyboardButton("📎 Басқару / Мақала / АКТ", callback_data="cat_3"),
    InlineKeyboardButton("💬 Психология / Курс / Семинар", callback_data="cat_4"),
    InlineKeyboardButton("🧾 Анықтама / Қолдау / Ашық сабақ", callback_data="cat_5"),
    InlineKeyboardButton("🎯 Сайыс / Авторлық / Басқа", callback_data="cat_6")
)

faq_submenus = {
    "cat_1": (
        "📚 *Пән бойынша сұрақтар:*\n\n"
        "🔢 Математика: \"Есеп шығаруға ми қайнай ма? Көмектесеміз!\"\n"
        "📖 Қазақ тілі: \"Тапсырмаларды безгекпен емес, жүйемен жасаңыз.\"\n"
        "🌍 Жаратылыстану: \"Сабақтар табиғаттай тірі болсын!\"\n"
        "🌐 Дүниетану: \"Әлемді танытатын сұрақтар осында.\"\n"
        "🔤 Әліппе: \"Әріптер әлеміне саяхат.\""
    ),
    "cat_2": (
        "📝 *Бағалау және сабақ жоспары:*\n\n"
        "📋 Сабақ жоспары: \"Жоспар – мұғалімнің GPS-і.\"\n"
        "📊 Бағалау: \"Әр бала – жеке әлем, бағалау да әділетті болсын!\""
    ),
    "cat_3": (
        "📎 *Сынып басқару, мақала, АКТ:*\n\n"
        "🧑‍🏫 Басқару: \"Сыныпта тәртіп – табыстың жартысы.\"\n"
        "📰 Мақала: \"Ойың бар ма? Жариялап жібер!\"\n"
        "💻 АКТ: \"Технология – сіздің көмекшіңіз.\""
    ),
    "cat_4": (
        "💬 *Психология, курс, семинар:*\n\n"
        "🧠 Психологиялық тренингтер: \"Жанға дем, сабаққа серпін.\"\n"
        "📚 Курс: \"Білімді жетілдіру ешқашан кеш емес.\"\n"
        "🎓 Семинарлар: \"Басқалармен бөлісу – үйренудің жартысы.\""
    ),
    "cat_5": (
        "🧾 *Анықтама, қолдау, ашық сабақ:*\n\n"
        "📑 Анықтама: \"Құжатпен мәселе туындаса – бізге жазыңыз.\"\n"
        "🙌 Қолдау: \"Курс біткен соң да бірге боламыз.\"\n"
        "🧑‍🏫 Ашық сабақ: \"Көрсететін сабақ – көрсеткішің.\""
    ),
    "cat_6": (
        "🎯 *Сайыстар және басқа сұрақтар:*\n\n"
        "🏆 Пед. идеялар сайысы: \"Шабытты мұғалім – үздік мұғалім.\"\n"
        "📘 Авторлық бағдарлама: \"Сіздің тәжірибеңіз – үлгіге лайық.\"\n"
        "❓ Басқа сұрақтар: \"Бәрін сұраңыз – жауап береміз!\""
    ),
}

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer(
        "🎓 *ӘДІСТЕМЕЛІК КӨМЕК БОТЫ*\n━━━━━━━━━━━━━━━━━━━━━\n"
        "🔊 *Сәлеметсіз бе, құрметті ұстаз!*\n\n"
        "Бұл бот бастауыш сынып мұғалімдеріне арналған.\n"
        "Мұндағы барлық ақпарат *авторлық бағдарлама негізінде* дайындалған.\n\n"
        "📚 Сізге көмектесе аламыз:\n"
        "✅ Сабақ жоспары\n"
        "✅ Бағалау жүйесі\n"
        "✅ Пәндік сұрақтар\n"
        "✅ Құжаттар мен анықтамалар\n"
        "✅ Психологиялық тренингтер\n"
        "✅ Семинарлар мен курс бойынша сұрақтар\n\n"
        "👇 Төмендегі мәзірден қажетті бөлімді таңдаңыз.",
        parse_mode="Markdown",
        reply_markup=main_kb
    )

@dp.message_handler(lambda message: message.text == "📄 Жиі қойылатын сұрақтар")
async def faq_handler(message: types.Message):
    await message.answer("🤔 Қай бөлім бойынша сұрағыңыз бар?", reply_markup=faq_main_kb)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("cat_"))
async def process_faq_category(callback_query: types.CallbackQuery):
    data = faq_submenus.get(callback_query.data)
    if data:
        await bot.send_message(callback_query.from_user.id, data[0], parse_mode="Markdown")
    await callback_query.answer()

# ====== FSM-заявка ====== #
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
