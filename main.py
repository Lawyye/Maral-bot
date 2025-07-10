import logging
import os
import re
import json
import time
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

# 🌐 Вебхук настройки
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://maral-bot.onrender.com")
WEBHOOK_PATH = "/webhook"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
Bot.set_current(bot)  # ИСПРАВЛЕНИЕ ОШИБКИ КОНТЕКСТА
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
@dp.message_handler(commands=['start'], state='*')
async def send_welcome(message: types.Message, state: FSMContext):
    """Обрабатывает команду /start и приветствует пользователя."""
    logging.info(f"🟢 START КОМАНДА ОТ ПОЛЬЗОВАТЕЛЯ {message.from_user.id}")
    
    # Сбрасываем любое активное состояние
    await state.finish()

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
@dp.message_handler(lambda msg: msg.text == "📝 Өтінім қалдыру", state='*')
async def start_request(message: types.Message, state: FSMContext):
    """Запускает процесс оформления заявки через FSM."""
    logging.info(f"🟡 ЗАЯВКА НАЧАТА ПОЛЬЗОВАТЕЛЕМ {message.from_user.id}")
    
    # Принудительно сбрасываем состояние
    await state.finish()
    
    await message.answer("📛 Атыңызды жазыңыз:")
    # Отправляем кнопку "Назад" отдельным сообщением
    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Басты мәзірге", callback_data="back_to_main"))
    await message.answer("_Басты мәзірге оралу үшін:_", parse_mode="Markdown", reply_markup=back_kb)
    await RequestForm.waiting_for_name.set()

@dp.message_handler(state=RequestForm.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    logging.info(f"🟡 ИМЯ ПОЛУЧЕНО: {message.text}")
    
    await state.update_data(name=message.text)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📲 Нөмірімді жіберу", request_contact=True))
    kb.add(KeyboardButton("✍️ Өзім жазамын"))
    await message.answer("📞 Телефон нөміріңізді жіберіңіз немесе түймені басыңыз:", reply_markup=kb)
    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Алдыңғы қадам", callback_data="back_to_name_prev"))
    await message.answer("_Артқа қайту үшін:_", parse_mode="Markdown", reply_markup=back_kb)
    await RequestForm.waiting_for_phone.set()

# НОВЫЙ обработчик для кнопки "✍️ Өзім жазамын"
@dp.message_handler(lambda msg: msg.text == "✍️ Өзім жазамын", state=RequestForm.waiting_for_phone)
async def manual_phone_entry(message: types.Message, state: FSMContext):
    """Обрабатывает выбор ручного ввода номера телефона."""
    logging.info(f"🟡 РУЧНОЙ ВВОД ТЕЛЕФОНА ВЫБРАН: пользователь {message.from_user.id}")
    
    await message.answer(
        "📝 Телефон нөміріңізді жазыңыз:\n"
        "_Мысалы: +7 (777) 123-45-67_",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Алдыңғы қадам", callback_data="back_to_name_prev"))
    await message.answer("_Артқа қайту үшін:_", parse_mode="Markdown", reply_markup=back_kb)

@dp.message_handler(content_types=types.ContentType.CONTACT, state=RequestForm.waiting_for_phone)
async def get_phone_contact(message: types.Message, state: FSMContext):
    """Обрабатывает отправленный контакт."""
    logging.info(f"🟡 КОНТАКТ ПОЛУЧЕН: {message.contact.phone_number}")
    await state.update_data(phone=message.contact.phone_number)

    await message.answer("📝 Сұрағыңызды толық сипаттап жазыңыз:", reply_markup=types.ReplyKeyboardRemove())

    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Алдыңғы қадам", callback_data="back_to_phone_prev"))
    await message.answer("_Артқа қайту үшін:_", parse_mode="Markdown", reply_markup=back_kb)

    await RequestForm.waiting_for_question.set()

@dp.message_handler(state=RequestForm.waiting_for_phone)
async def get_phone_text(message: types.Message, state: FSMContext):
    """Обрабатывает введенный вручную номер телефона."""
    # Проверяем, что это не кнопка "✍️ Өзім жазамын"
    if message.text == "✍️ Өзім жазамын":
        return  # Обработается специальным хендлером выше
    
    logging.info(f"🟡 ТЕЛЕФОН ТЕКСТОМ: {message.text}")
    await state.update_data(phone=message.text)

    await message.answer("📝 Сұрағыңызды толық сипаттап жазыңыз:", reply_markup=types.ReplyKeyboardRemove())

    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Алдыңғы қадам", callback_data="back_to_phone_prev"))
    await message.answer("_Артқа қайту үшін:_", parse_mode="Markdown", reply_markup=back_kb)

    await RequestForm.waiting_for_question.set()

@dp.message_handler(state=RequestForm.waiting_for_question)
async def get_question(message: types.Message, state: FSMContext):
    """Получает вопрос пользователя, отправляет админу и завершает FSM."""
    logging.info(f"🟡 ВОПРОС ПОЛУЧЕН ОТ {message.from_user.id}: {message.text}")
    
    try:
        user_data = await state.get_data()
        name = user_data.get('name', 'Не указано')
        phone = user_data.get('phone', 'Не указано')
        question = message.text

        logging.info(f"🟡 ДАННЫЕ: имя={name}, телефон={phone}")

        # Исправление: выносим re.sub в отдельную переменную
        wa_phone = re.sub(r'[^\d]', '', phone)

        # Формируем сообщение для админа
        admin_text = (
            f"📥 *Жаңа өтінім!*\n\n"
            f"👤 *Аты:* {name}\n"
            f"📞 *Телефон:* {phone}\n"
            f"❓ *Сұрақ:* {question}\n\n"
            f"📱 [WhatsApp-қа өту](https://wa.me/{wa_phone})"
        )

        try:
            # Отправляем админу
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID, 
                text=admin_text, 
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            logging.info(f"✅ СООБЩЕНИЕ ОТПРАВЛЕНО АДМИНУ {ADMIN_CHAT_ID}")
        except Exception as e:
            logging.error(f"❌ ОШИБКА ОТПРАВКИ АДМИНУ: {e}")

        # Подтверждаем пользователю
        await message.answer(
            "✅ *Рақмет!*\n\n"
            "Сіздің өтінішіңіз қабылданды және маманға жіберілді.\n"
            "Жауап 24 сағат ішінде беріледі.\n\n"
            "_Басты мәзірге оралу үшін /start командасын басыңыз_",
            parse_mode="Markdown",
            reply_markup=main_kb
        )

        logging.info(f"✅ ЗАЯВКА ЗАВЕРШЕНА ДЛЯ {message.from_user.id}")

    except Exception as e:
        logging.error(f"❌ ОШИБКА В get_question: {e}")
        await message.answer(
            "❌ Қате пайда болды. Қайта көріңіз немесе /start басыңыз.",
            reply_markup=main_kb
        )
    finally:
        # ВСЕГДА завершаем FSM
        await state.finish()

# Обработчики inline-кнопок назад для FSM
@dp.callback_query_handler(lambda c: c.data == "back_to_main", state='*')
async def back_to_main_menu(callback_query: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню из любого состояния."""
    await state.finish()

    # Удаляем inline-клавиатуру
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback_query.answer("Басты мәзірге оралдыңыз ✅")

    # Отправляем сообщение с главным меню
    await callback_query.message.answer(
        "Басты мәзір:",
        reply_markup=main_kb
    )

@dp.callback_query_handler(lambda c: c.data == "back_to_name_prev", state=RequestForm.waiting_for_phone)
async def back_to_name_step(callback_query: types.CallbackQuery, state: FSMContext):
    """Возврат к шагу ввода имени из шага телефона."""
    # Удаляем inline-клавиатуру
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback_query.answer("Алдыңғы қадамға оралдыңыз")

    # Возвращаемся к вводу имени
    await RequestForm.waiting_for_name.set()

    await callback_query.message.answer("📛 Атыңызды жазыңыз:")

    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Басты мәзірге", callback_data="back_to_main"))
    await callback_query.message.answer("_Басты мәзірге оралу үшін:_", parse_mode="Markdown", reply_markup=back_kb)

@dp.callback_query_handler(lambda c: c.data == "back_to_phone_prev", state=RequestForm.waiting_for_question)
async def back_to_phone_step(callback_query: types.CallbackQuery, state: FSMContext):
    """Возврат к шагу ввода телефона из шага вопроса."""
    # Удаляем inline-клавиатуру
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback_query.answer("Алдыңғы қадамға оралдыңыз")

    # Возвращаемся к вводу телефона
    await RequestForm.waiting_for_phone.set()

    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📲 Нөмірімді жіберу", request_contact=True))
    kb.add(KeyboardButton("✍️ Өзім жазамын"))

    await callback_query.message.answer("📞 Телефон нөміріңізді жіберіңіз немесе түймені басыңыз:", reply_markup=kb)

    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Алдыңғы қадам", callback_data="back_to_name_prev"))
    await callback_query.message.answer("_Артқа қайту үшін:_", parse_mode="Markdown", reply_markup=back_kb)

# FAQ (первый уровень)
@dp.message_handler(lambda msg: msg.text == "📄 Жиі қойылатын сұрақтар", state='*')
async def show_faq_categories(message: types.Message, state: FSMContext):
    """Показывает категории FAQ через inline-клавиатуру."""
    logging.info(f"🔵 FAQ ЗАПРОШЕН ПОЛЬЗОВАТЕЛЕМ {message.from_user.id}")
    
    # Сбрасываем состояние
    await state.finish()
    
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

    # Кнопка "Назад" отдельным сообщением
    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Басты мәзірге", callback_data="faq_back_to_main"))
    await message.answer("_Басты мәзірге оралу үшін:_", parse_mode="Markdown", reply_markup=back_kb)

@dp.callback_query_handler(lambda c: c.data.startswith("faq_"), state='*')
async def show_faq_detail(callback_query: types.CallbackQuery, state: FSMContext):
    """Показывает подробности выбранной категории FAQ."""
    logging.info(f"🔵 FAQ CALLBACK: {callback_query.data}")
    
    # Сбрасываем состояние на всякий случай
    await state.finish()
    
    # Удаляем старую клавиатуру
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    if callback_query.data == "faq_back_to_main":
        await callback_query.answer("Басты мәзірге оралдыңыз ✅")
        await callback_query.message.answer("Басты мәзір:", reply_markup=main_kb)
        return

    elif callback_query.data == "faq_back_to_categories":
        await callback_query.answer("Категорияларға оралдыңыз")
        # Показываем категории снова
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("📚 Пән бойынша", callback_data="faq_subjects"),
            InlineKeyboardButton("📝 Бағалау / Сабақ", callback_data="faq_assessment"),
            InlineKeyboardButton("📎 Басқару / Мақала", callback_data="faq_docs"),
            InlineKeyboardButton("💬 Психология / Курс", callback_data="faq_psy"),
            InlineKeyboardButton("🧾 Анықтама / Ашық сабақ", callback_data="faq_cert"),
            InlineKeyboardButton("🎯 Сайыс / Авторлық", callback_data="faq_other")
        )
        await callback_query.message.answer("🤔 Қай бөлім бойынша сұрағыңыз бар?", reply_markup=kb)

        back_kb = InlineKeyboardMarkup()
        back_kb.add(InlineKeyboardButton("⬅️ Басты мәзірге", callback_data="faq_back_to_main"))
        await callback_query.message.answer("_Басты мәзірге оралу үшін:_", parse_mode="Markdown", reply_markup=back_kb)
        return

    # Данные для категорий
    faq_data = {
        "faq_subjects": (
            "📚 *Пән бойынша сұрақтар:*\n\n"
            "• *Математика* - есептеу дағдылары, логикалық тапсырмалар\n"
            "• *Қазақ тілі* - грамматика, орфография, сөйлеу дағдылары\n"
            "• *Әдебиеттік оқу* - мәнерлеп оқу, мәтінмен жұмыс\n"
            "• *Жаратылыстану* - зерттеу жұмыстары, тәжірибелер\n"
            "• *Дүниетану* - жобалық жұмыстар, презентациялар\n"
            "• *Әліппе* - дыбыстық талдау, жазу дағдылары"
        ),
        "faq_assessment": (
            "📝 *Бағалау мен сабақ жоспары:*\n\n"
            "• *Сабақ құрылымы* - кезеңдері, уақытты бөлу\n"
            "• *Қалыптастырушы бағалау* - әдістері, құралдары\n"
            "• *Жиынтық бағалау* - БЖБ, ТЖБ өткізу\n"
            "• *Кері байланыс* - тиімді әдістері\n"
            "• *Дескрипторлар* - құрастыру жолдары\n"
            "• *Кеңейтілген дағдылар* - енгізу тәсілдері"
        ),
        "faq_docs": (
            "📎 *Құжаттар / Мақала / Басқару:*\n\n"
            "• *Сыныпты басқару* - тәртіп, мотивация\n"
            "• *Құжат жүргізу* - журнал, жоспарлар\n"
            "• *Мақала жариялау* - республикалық басылымдар\n"
            "• *Ата-аналармен жұмыс* - кеңестер, жиналыстар\n"
            "• *Портфолио* - дайындау, рәсімдеу"
        ),
        "faq_psy": (
            "💬 *Психологиялық тренингтер мен курс:*\n\n"
            "• *Балалармен тренингтер* - өзін-өзі тану, достық\n"
            "• *Ата-аналарға арналған* - тәрбие, қарым-қатынас\n"
            "• *Мұғалімдерге* - кәсіби қиындықтардын алдын алу\n"
            "• *Курстар* - біліктілікті арттыру\n"
            "• *Семинарлар* - заманауи әдістер"
        ),
        "faq_cert": (
            "🧾 *Анықтама / Ашық сабақ:*\n\n"
            "• *Ашық сабақ* - дайындық, өткізу кезеңдері\n"
            "• *Сабақ талдау* - өзін-өзі талдау схемасы\n"
            "• *Анықтама алу* - қажетті құжаттар\n"
            "• *Мінездеме* - жазу үлгілері\n"
            "• *Грамота, алғыс хат* - рәсімдеу"
        ),
        "faq_other": (
            "🎯 *Сайыс / Авторлық бағдарлама:*\n\n"
            "• *Педагогикалық идеялар* - 'Үздік педагог', 'педагогикалық идеялар панорамасы' сайысы\n"
            "• *Авторлық бағдарлама* - құрастыру, қорғау\n"
            "• *Аттестация* - дайындық, құжаттар\n"
            "• *Ғылыми жобалар* - оқушылармен жұмыс\n"
            "• *Инновациялық әдістер* - енгізу тәжірибесі"
        )
    }

    text = faq_data.get(callback_query.data, "Кешіріңіз, ақпарат табылмады.")
    await callback_query.answer("Ақпарат жүктелді ✅")
    await callback_query.message.answer(text, parse_mode="Markdown")

    # Кнопка назад к категориям
    back_kb = InlineKeyboardMarkup()
    back_kb.add(InlineKeyboardButton("⬅️ Категорияларға", callback_data="faq_back_to_categories"))
    await callback_query.message.answer("_Артқа қайту үшін:_", parse_mode="Markdown", reply_markup=back_kb)

# Команды для диагностики
@dp.message_handler(commands=['ping'])
async def ping_handler(message: types.Message):
    """Проверка работы бота."""
    await message.answer("🟢 Бот жұмыс істеп тұр!")

@dp.message_handler(commands=['menu'], state='*')
async def show_main_menu(message: types.Message, state: FSMContext):
    """Команда /menu: сбрасывает все состояния и показывает главное меню."""
    await state.finish()
    await message.answer("Басты мәзір:", reply_markup=main_kb)

@dp.message_handler(commands=['reset'], state='*')
async def reset_bot(message: types.Message, state: FSMContext):
    """Полный сброс состояния бота."""
    await state.finish()
    await message.answer(
        "♻️ Бот толық қайта іске қосылды.\n"
        "Басты мәзірге ораламыз...",
        reply_markup=main_kb
    )

# ВАЖНО: Fallback обработчик для всех сообщений вне состояний
@dp.message_handler(state='*')
async def fallback_handler(message: types.Message, state: FSMContext):
    """Обрабатывает все сообщения, которые не попали в другие хендлеры."""
    logging.info(f"🔴 FALLBACK: {message.text} от {message.from_user.id}")
    
    # Получаем текущее состояние
    current_state = await state.get_state()
    
    if current_state:
        # Если есть активное состояние, говорим об этом
        await message.answer(
            "❓ Сіз қазір заявканы толтыру процесінде тұрсыз.\n"
            "Басты мәзірге оралу үшін /start басыңыз немесе процесті жалғастырыңыз.",
            reply_markup=main_kb
        )
    else:
        # Если состояния нет, показываем главное меню
        await message.answer(
            "❓ Түсініксіз команда.\n"
            "Мәзірден қажетті опцияны таңдаңыз:",
            reply_markup=main_kb
        )

# Обработчик неизвестных callback-запросов
@dp.callback_query_handler(lambda c: True, state='*')
async def handle_unknown_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик для неизвестных callback-кнопок."""
    logging.info(f"🔴 UNKNOWN CALLBACK: {callback_query.data}")
    await callback_query.answer("Белгісіз команда. Қайта көріңіз.", show_alert=True)

# Глобальный обработчик ошибок
@dp.errors_handler()
async def global_error_handler(update, exception):
    """Глобальный обработчик ошибок для логирования."""
    logging.error(f"❌ ГЛОБАЛЬНАЯ ОШИБКА в update {update}: {exception}")
    
    # Пытаемся отправить сообщение об ошибке пользователю
    try:
        if update.message:
            await update.message.answer(
                "❌ Техникалық қате. /start басып қайта көріңіз.",
                reply_markup=main_kb
            )
    except Exception:
        pass
    
    return True

# ========== ИСПРАВЛЕННЫЙ WEBHOOK ОБРАБОТЧИК ==========
async def webhook_handler(request):
    """Кастомный обработчик webhook с подробным логированием."""
    try:
        # Получаем тело запроса
        body = await request.text()
        logging.info(f"🔵 WEBHOOK ПОЛУЧЕН: {len(body)} символов")
        
        if not body:
            logging.warning("⚠️ ПУСТОЕ ТЕЛО ЗАПРОСА")
            return web.Response(text="Empty body", status=400)
        
        # Парсим JSON
        try:
            json_data = json.loads(body)
            logging.info(f"✅ JSON ПАРСИНГ УСПЕШЕН")
        except json.JSONDecodeError as e:
            logging.error(f"❌ ОШИБКА ПАРСИНГА JSON: {e}")
            return web.Response(text="Invalid JSON", status=400)
        
        # Создаем объект Update
        try:
            update = types.Update(**json_data)
            logging.info(f"✅ UPDATE СОЗДАН: update_id={update.update_id}")
            
            if update.message:
                user = update.message.from_user
                logging.info(f"📩 СООБЩЕНИЕ ОТ: @{user.username} (ID: {user.id})")
                logging.info(f"📝 ТЕКСТ: {update.message.text}")
            elif update.callback_query:
                logging.info(f"🔘 CALLBACK: {update.callback_query.data}")
                
        except Exception as e:
            logging.error(f"❌ ОШИБКА СОЗДАНИЯ UPDATE: {e}")
            return web.Response(text="Invalid update", status=400)
        
        # Обрабатываем через диспетчер
        try:
            await dp.process_update(update)
            logging.info(f"✅ UPDATE ОБРАБОТАН УСПЕШНО")
            return web.Response(text="OK")
            
        except Exception as e:
            logging.error(f"❌ ОШИБКА ОБРАБОТКИ UPDATE: {e}")
            return web.Response(text="Processing error", status=500)
            
    except Exception as e:
        logging.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА В WEBHOOK: {e}")
        return web.Response(text="Internal server error", status=500)

# ========== ЗАПУСК СЕРВЕРА ==========
async def on_startup(app):
    """Инициализация при запуске."""
    try:
        # Устанавливаем webhook
        await bot.set_webhook(WEBHOOK_URL)
        logging.info(f"🚀 WEBHOOK УСТАНОВЛЕН: {WEBHOOK_URL}")
        
        # Проверяем webhook
        webhook_info = await bot.get_webhook_info()
        logging.info(f"📋 WEBHOOK INFO: {webhook_info}")
        
    except Exception as e:
        logging.error(f"❌ ОШИБКА УСТАНОВКИ WEBHOOK: {e}")

async def on_shutdown(app):
    """Очистка при завершении."""
    try:
        await bot.delete_webhook()
        logging.info("🔴 WEBHOOK УДАЛЕН")
        await dp.storage.close()
        await dp.storage.wait_closed()
        logging.info("🔴 STORAGE ЗАКРЫТ")
    except Exception as e:
        logging.error(f"❌ ОШИБКА ПРИ ЗАВЕРШЕНИИ: {e}")

if __name__ == '__main__':
    # Создаем веб-приложение
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, webhook_handler)
    
    # Добавляем startup/shutdown handlers
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    # Запускаем сервер
    logging.info(f"🚀 ЗАПУСК СЕРВЕРА НА {WEBAPP_HOST}:{WEBAPP_PORT}")
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)