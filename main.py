
import logging
import os
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv
from aiohttp import web

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 584791919

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# FSM форма
class RequestForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_question = State()

# Клавиатура
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(
    KeyboardButton("📄 Жиі қойылатын сұрақтар"),
    KeyboardButton("📝 Өтінім қалдыру")
)

# START
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer(
        "🎓 *ӘДІСТЕМЕЛІК КӨМЕК БОТЫ*
"
        "━━━━━━━━━━━━━━━━━━━━━
"
        "🔊 Сәлеметсіз бе, құрметті ұстаз!

"
        "Бұл бот бастауыш сынып мұғалімдеріне арналған.
"
        "Мұндағы барлық ақпарат *бастауыш білім беру стандарты* негізінде дайындалған.

"
        "📚 *Сізге көмектесе аламыз:*
"
        "✅ Сабақ жоспары (сабақтың кезеңдері, аспектілері, құндылықтар, кеңейтілген дағдыларды енгізу)
"
        "✅ Бағалау жүйесі (қалыптастырушы бағалау, бақылау, бағалау түрлері)
"
        "✅ Пәндік сұрақтар (математика, қазақ тілі, әдебиет, жаратылыстану, дүниетану)
"
        "✅ Құжаттар мен анықтамалар
"
        "✅ Психологиялық тренингтер
"
        "✅ Семинарлар мен курс бойынша сұрақтар
"
        "✅ Авторлық бағдарлама бойынша кеңес (қандай идеялар тиімді)
"
        "✅ Аттестаттау және анықтама алу жолдары

"
        "📲 *Қалай байланысуға болады?*
"
        "Төмендегі мәзірден қажетті бөлімді таңдаңыз немесе оң жақтағы мәзірді басып, WhatsApp-қа шығыңыз.
"
        "Жауап 24 сағаттың ішінде беріледі.",
        parse_mode="Markdown",
        reply_markup=main_kb
    )

# FSM диалог
@dp.message_handler(lambda msg: msg.text == "📝 Өтінім қалдыру")
async def start_request(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📲 Нөмірімді жіберу", request_contact=True))
    kb.add(KeyboardButton("✍️ Өзім жазамын"))
    await message.answer("📛 Атыңызды жазыңыз:", reply_markup=kb)
    await RequestForm.waiting_for_name.set()

@dp.message_handler(state=RequestForm.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📲 Нөмірімді жіберу", request_contact=True))
    await message.answer("📞 Телефон нөміріңізді жіберіңіз немесе түймені басыңыз:", reply_markup=kb)
    await RequestForm.waiting_for_phone.set()

@dp.message_handler(content_types=types.ContentType.CONTACT, state=RequestForm.waiting_for_phone)
async def get_phone_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("📝 Сұрағыңызды толық сипаттап жазыңыз:")
    await RequestForm.waiting_for_question.set()

@dp.message_handler(state=RequestForm.waiting_for_phone)
async def get_phone_text(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("📝 Сұрағыңызды толық сипаттап жазыңыз:")
    await RequestForm.waiting_for_question.set()

@dp.message_handler(state=RequestForm.waiting_for_question)
async def get_question(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data['name']
    phone = user_data['phone']
    question = message.text

    text = (
        f"📥 *Жаңа өтінім!*

"
        f"👤 Аты: {name}
"
        f"📞 Телефон: {phone}
"
        f"📝 Сұрақ: {question}
"
        f"📲 WhatsApp: https://wa.me/{''.join(filter(str.isdigit, phone))}"
    )

    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode="Markdown")
    await message.answer("✅ Рақмет! Сұранысыңыз жіберілді.")
    await state.finish()

# FAQ (первый уровень)
@dp.message_handler(lambda msg: msg.text == "📄 Жиі қойылатын сұрақтар")
async def show_faq_categories(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📚 Пән бойынша", callback_data="faq_subjects"),
        InlineKeyboardButton("📝 Бағалау / Сабақ", callback_data="faq_assessment"),
        InlineKeyboardButton("📎 Басқару / Мақала", callback_data="faq_docs"),
        InlineKeyboardButton("💬 Психология / Курс", callback_data="faq_psy"),
        InlineKeyboardButton("🧾 Анықтама / Ашық сабақ", callback_data="faq_cert"),
        InlineKeyboardButton("🎯 Сайыс / Авторлық", callback_data="faq_other")
    )
    await message.answer("🤔 Қай бөлім бойынша сұрағыңыз бар?", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("faq_"))
async def show_faq_detail(callback_query: types.CallbackQuery):
    data = {
        "faq_subjects": "📚 *Пән бойынша сұрақтар:*
- Математика
- Қазақ тілі
- Жаратылыстану
- Дүниетану
- Әліппе",
        "faq_assessment": "📝 *Бағалау мен сабақ жоспары:*
- Сабақ құрылымы
- Бағалау түрлері
- Кеңейтілген дағдылар",
        "faq_docs": "📎 *Құжаттар / Мақала / Басқару:*
- Сыныпты басқару
- Құжат жүргізу
- Мақала жариялау",
        "faq_psy": "💬 *Психологиялық тренингтер мен курс:*
- Тренинг үлгілері
- Курстардан алған әдістер",
        "faq_cert": "🧾 *Анықтама / Ашық сабақ:*
- Ашық сабақ үлгілері
- Анықтама рәсімдеу жолдары",
        "faq_other": "🎯 *Сайыс / Авторлық бағдарлама:*
- Педагогикалық идеялар сайысы
- Авторлық бағдарлама
- Аттестация сұрақтары"
    }
    text = data.get(callback_query.data, "Қате кетті...")
    await callback_query.message.answer(text, parse_mode="Markdown")

# Anti-sleep web server
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
