
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
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

if not TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")
if not ADMIN_CHAT_ID:
    raise ValueError("ADMIN_CHAT_ID is not set in environment variables")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# FSM форма
class RequestForm(StatesGroup):
    """Состояния для формы заявки пользователя."""
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
    """Обрабатывает команду /start и приветствует пользователя."""
    await message.answer(
        "🎓 *ӘДІСТЕМЕЛІК КӨМЕК БОТЫ*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🔊 Сәлеметсіз бе, құрметті ұстаз!\n\n"
        "Бұл бот бастауыш сынып мұғалімдеріне арналған.\n"
        "Мұндағы барлық ақпарат *бастауыш білім беру стандарты* негізінде дайындалған.\n\n"
        "📚 *Сізге көмектесе аламыз:*\n"
        "✅ Сабақ жоспары (сабақтың кезеңдері, аспектілері, құндылықтар, кеңейтілген дағдыларды енгізу)\n"
        "✅ Бағалау жүйесі (қалыптастырушы бағалау, бақылау, бағалау түрлері)\n"
        "✅ Пәндік сұрақтар (математика, қазақ тілі, әдебиет, жаратылыстану, дүниетану)\n"
        "✅ Құжаттар мен анықтамалар\n"
        "✅ Психологиялық тренингтер\n"
        "✅ Семинарлар мен курс бойынша сұрақтар\n"
        "✅ Авторлық бағдарлама бойынша кеңес (қандай идеялар тиімді)\n"
        "✅ Аттестаттау және анықтама алу жолдары\n\n"
        "📲 *Қалай байланысуға болады?*\n"
        "Төмендегі мәзірден қажетті бөлімді таңдаңыз немесе оң жақтағы мәзірді басып, WhatsApp-қа шығыңыз.\n"
        "Жауап 24 сағаттың ішінде беріледі.",
        parse_mode="Markdown",
        reply_markup=main_kb
    )

# FSM диалог
@dp.message_handler(lambda msg: msg.text == "📝 Өтінім қалдыру")
async def start_request(message: types.Message):
    """Запускает процесс оформления заявки через FSM."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📲 Нөмірімді жіберу", request_contact=True))
    kb.add(KeyboardButton("✍️ Өзім жазамын"))
    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main"))
    await message.answer("📛 Атыңызды жазыңыз:", reply_markup=kb)
    await message.answer("Кері қайту үшін төмендегі батырманы басыңыз:", reply_markup=back_kb)
    await RequestForm.waiting_for_name.set()

@dp.message_handler(state=RequestForm.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    """Получает имя пользователя и запрашивает телефон."""
    await state.update_data(name=message.text)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📲 Нөмірімді жіберу", request_contact=True))
    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_name_prev"))
    await message.answer("📞 Телефон нөміріңізді жіберіңіз немесе түймені басыңыз:", reply_markup=kb)
    await message.answer("Кері қайту үшін төмендегі батырманы басыңыз:", reply_markup=back_kb)
    await RequestForm.waiting_for_phone.set()

@dp.message_handler(content_types=types.ContentType.CONTACT, state=RequestForm.waiting_for_phone)
async def get_phone_contact(message: types.Message, state: FSMContext):
    """Получает телефон через контакт и запрашивает вопрос."""
    await state.update_data(phone=message.contact.phone_number)
    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_phone_prev"))
    await message.answer("📝 Сұрағыңызды толық сипаттап жазыңыз:")
    await message.answer("Кері қайту үшін төмендегі батырманы басыңыз:", reply_markup=back_kb)
    await RequestForm.waiting_for_question.set()

@dp.message_handler(state=RequestForm.waiting_for_phone)
async def get_phone_text(message: types.Message, state: FSMContext):
    """Получает телефон, введённый текстом, и запрашивает вопрос."""
    await state.update_data(phone=message.text)
    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_phone_prev"))
    await message.answer("📝 Сұрағыңызды толық сипаттап жазыңыз:")
    await message.answer("Кері қайту үшін төмендегі батырманы басыңыз:", reply_markup=back_kb)
    await RequestForm.waiting_for_question.set()

@dp.message_handler(state=RequestForm.waiting_for_question)
async def get_question(message: types.Message, state: FSMContext):
    """Получает вопрос пользователя, отправляет админу и завершает FSM."""
    user_data = await state.get_data()
    name = user_data['name']
    phone = user_data['phone']
    question = message.text

    text = (
        f"📥 *Жаңа өтінім!*\n\n"
        f"👤 Аты: {name}\n"
        f"📞 Телефон: {phone}\n"
        f"📝 Сұрақ: {question}\n"
        f"📲 WhatsApp: https://wa.me/{''.join(filter(str.isdigit, phone))}"
    )

    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode="Markdown")
    await message.answer("✅ Рақмет! Сұранысыңыз жіберілді.")
    await state.finish()

# Обработчики inline-кнопок назад для FSM (мастер-стиль)
@dp.callback_query_handler(lambda c: c.data == "back_to_main")
async def back_to_main_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    # Удаляем inline-клавиатуру у предыдущего сообщения
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    # Проверяем, не в главном ли меню уже пользователь
    if callback_query.message.reply_markup is None:
        await callback_query.answer("Сіз басты мәзірдесіз.")
        return
    await callback_query.message.answer(
        "Сіз басты мәзірге оралдыңыз.",
        reply_markup=main_kb
    )

@dp.callback_query_handler(lambda c: c.data == "back_to_name_prev")
async def back_to_name_step(callback_query: types.CallbackQuery, state: FSMContext):
    """Возврат к шагу ввода имени из шага телефона."""
    await RequestForm.waiting_for_name.set()
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📲 Нөмірімді жіберу", request_contact=True))
    kb.add(KeyboardButton("✍️ Өзім жазамын"))
    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main"))
    await callback_query.message.answer("📛 Атыңызды жазыңыз:", reply_markup=kb)
    await callback_query.message.answer("Кері қайту үшін төмендегі батырманы басыңыз:", reply_markup=back_kb)

@dp.callback_query_handler(lambda c: c.data == "back_to_phone_prev")
async def back_to_phone_step(callback_query: types.CallbackQuery, state: FSMContext):
    """Возврат к шагу ввода телефона из шага вопроса."""
    await RequestForm.waiting_for_phone.set()
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📲 Нөмірімді жіберу", request_contact=True))
    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_name_prev"))
    await callback_query.message.answer("📞 Телефон нөміріңізді жіберіңіз немесе түймені басыңыз:", reply_markup=kb)
    await callback_query.message.answer("Кері қайту үшін төмендегі батырманы басыңыз:", reply_markup=back_kb)

# FAQ (первый уровень)
@dp.message_handler(lambda msg: msg.text == "📄 Жиі қойылатын сұрақтар")
async def show_faq_categories(message: types.Message):
    """Показывает категории FAQ через inline-клавиатуру."""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📚 Пән бойынша", callback_data="faq_subjects"),
        InlineKeyboardButton("📝 Бағалау / Сабақ", callback_data="faq_assessment"),
        InlineKeyboardButton("📎 Басқару / Мақала", callback_data="faq_docs"),
        InlineKeyboardButton("💬 Психология / Курс", callback_data="faq_psy"),
        InlineKeyboardButton("🧾 Анықтама / Ашық сабақ", callback_data="faq_cert"),
        InlineKeyboardButton("🎯 Сайыс / Авторлық", callback_data="faq_other")
    )
    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="faq_back_to_main"))
    await message.answer("🤔 Қай бөлім бойынша сұрағыңыз бар?", reply_markup=kb)
    await message.answer("Кері қайту үшін төмендегі батырманы басыңыз:", reply_markup=back_kb)

@dp.callback_query_handler(lambda c: c.data.startswith("faq_"))
async def show_faq_detail(callback_query: types.CallbackQuery):
    """Показывает подробности выбранной категории FAQ."""
    if callback_query.data == "faq_back_to_main":
        await callback_query.message.answer("Сіз басты мәзірге оралдыңыз.", reply_markup=main_kb)
        return
    elif callback_query.data == "faq_back_to_categories":
        # Обработка возврата к категориям FAQ
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("📚 Пән бойынша", callback_data="faq_subjects"),
            InlineKeyboardButton("📝 Бағалау / Сабақ", callback_data="faq_assessment"),
            InlineKeyboardButton("📎 Басқару / Мақала", callback_data="faq_docs"),
            InlineKeyboardButton("💬 Психология / Курс", callback_data="faq_psy"),
            InlineKeyboardButton("🧾 Анықтама / Ашық сабақ", callback_data="faq_cert"),
            InlineKeyboardButton("🎯 Сайыс / Авторлық", callback_data="faq_other")
        )
        back_kb = InlineKeyboardMarkup()
        back_kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="faq_back_to_main"))
        await callback_query.message.answer("🤔 Қай бөлім бойынша сұрағыңыз бар?", reply_markup=kb)
        await callback_query.message.answer("Кері қайту үшін төмендегі батырманы басыңыз:", reply_markup=back_kb)
        return
    
    data = {
        "faq_subjects": "📚 *Пән бойынша сұрақтар:*\n- Математика\n- Қазақ тілі\n- Жаратылыстану\n- Дүниетану\n- Әліппе",
        "faq_assessment": "📝 *Бағалау мен сабақ жоспары:*\n- Сабақ құрылымы\n- Бағалау түрлері\n- Кеңейтілген дағдылар",
        "faq_docs": "📎 *Құжаттар / Мақала / Басқару:*\n- Сыныпты басқару\n- Құжат жүргізу\n- Мақала жариялау",
        "faq_psy": "💬 *Психологиялық тренингтер мен курс:*\n- Тренинг үлгілері\n- Курстардан алған әдістер",
        "faq_cert": "🧾 *Анықтама / Ашық сабақ:*\n- Ашық сабақ үлгілері\n- Анықтама рәсімдеу жолдары",
        "faq_other": "🎯 *Сайыс / Авторлық бағдарлама:*\n- Педагогикалық идеялар сайысы\n- Авторлық бағдарлама\n- Аттестация сұрақтары"
    }
    text = data.get(callback_query.data, "Қате кетті...")
    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="faq_back_to_categories"))
    await callback_query.message.answer(text, parse_mode="Markdown", reply_markup=back_kb)

# Универсальный обработчик для всех остальных callback-кнопок
@dp.callback_query_handler(lambda c: True)
async def handle_unknown_callback(callback_query: types.CallbackQuery):
    """Обработчик для неизвестных callback-кнопок."""
    await callback_query.answer("Кнопка не работает. Попробуйте еще раз.")

# Глобальный обработчик ошибок
@dp.errors_handler()
async def global_error_handler(update, exception):
    """Глобальный обработчик ошибок для логирования."""
    logging.error(f"Exception: {exception}")
    return True

# Anti-sleep web server
async def web_handler(request):
    """Обработчик для проверки работы бота через веб-сервер."""
    return web.Response(text="Bot is running!")

async def web_server():
    """Запускает aiohttp веб-сервер для anti-sleep."""
    app = web.Application()
    app.router.add_get('/', web_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get('PORT', 8080)))
    await site.start()

async def main():
    """Основная точка входа: запускает веб-сервер и polling aiogram."""
    await asyncio.gather(
        web_server(),
        dp.start_polling()
    )

if __name__ == '__main__':
    asyncio.run(main())
