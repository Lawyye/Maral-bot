import logging
import os
import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 584791919  # Telegram ID мамы

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Машина состояний
class RequestForm(StatesGroup):
    name = State()
    phone = State()
    question = State()

# Главное меню
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(
    KeyboardButton("\ud83d\udcc4 \u0416\u0438\u0456 \u049b\u043e\u0439\u044b\u043b\u0430\u0442\u044b\u043d \u0441\u04b1\u0440\u0430\u049b\u0442\u0430\u0440"),
    KeyboardButton("\ud83d\udcdd \u04e8\u0442\u0456\u043d\u0456\u043c \u049b\u0430\u043b\u0434\u044b\u0440\u0443")
)

# Старт
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer(
        "\u0421\u04d9\u043b\u0435\u043c\u0435\u0442\u0441\u0456\u0437 \u0431\u0435! \u0411\u04b1\u043b \u0431\u043e\u0442 \u0431\u0430\u0441\u0442\u0430\u0443\u044b\u0448 \u0441\u044b\u043d\u044b\u043f \u043c\u04b1\u0493\u0430\u043b\u0456\u043c\u0434\u0435\u0440\u0456\u043d\u0435 \u04d9\u0434\u0456\u0441\u0442\u0435\u043c\u0435\u043b\u0456\u043a \u043a\u04e9\u043c\u0435\u043a \u043a\u04e9\u0440\u0441\u0435\u0442\u0443 \u04af\u0448\u0456\u043d \u0436\u0430\u0441\u0430\u043b\u0493\u0430\u043d. \n\u0422\u04e9\u043c\u0435\u043d\u043d\u0435\u043d \u049b\u0430\u0436\u0435\u0442\u0442\u0456 \u0431\u04e9\u043b\u0456\u043c\u0434\u0456 \u0442\u0430\u04a3\u0434\u0430\u04a3\u044b\u0437:",
        reply_markup=main_kb
    )

# Жиі сұрақтар
@dp.message_handler(lambda message: message.text == "\ud83d\udcc4 \u0416\u0438\u0456 \u049b\u043e\u0439\u044b\u043b\u0430\u0442\u044b\u043d \u0441\u04b1\u0440\u0430\u049b\u0442\u0430\u0440")
async def faq_handler(message: types.Message):
    await message.answer(
        "\ud83e\udd14 *\u0416\u0438\u0456 \u049b\u043e\u0439\u044b\u043b\u0430\u0442\u044b\u043d \u0441\u04b1\u0440\u0430\u049b\u0442\u0430\u0440:*\n\n"
        "1. Сабақ жоспары бойынша сұрақтар\n"
        "2. Бағалау бойынша сұрақтар\n"
        "3. Пән бойынша сұрақтар: Математика, Қазақ тілі, Жаратылыстану, Дүниетану, Әліппе\n"
        "4. Мақала жариялау\n5. Сыныпты басқару\n6. АКТ\n7. Психологиялық тренингтер\n8. Курс бойынша сұрақтар\n9. Семинарлар\n10. Анықтама\n11. Курстан кейінгі қолдау\n12. Ашық сабақ\n13. Педагогикалық идеялар сайысы\n14. Авторлық бағдарлама\n15. Басқа да сұрақтар\n\n"
        "\ud83d\udc69\u200d\ud83c\udfeb Сіздің өтіліңіз қанша жыл?",
        parse_mode="Markdown"
    )

# Заявка: начало
@dp.message_handler(lambda message: message.text == "\ud83d\udcdd \u04e8\u0442\u0456\u043d\u0456\u043c \u049b\u0430\u043b\u0434\u044b\u0440\u0443")
async def start_request(message: types.Message):
    await message.answer("\ud83d\udc64 Атыңызды жазыңыз:", reply_markup=ReplyKeyboardRemove())
    await RequestForm.name.set()

@dp.message_handler(state=RequestForm.name)
async def request_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    contact_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    contact_kb.add(KeyboardButton("\ud83d\udcde Нөмірімді жіберу", request_contact=True))
    contact_kb.add(KeyboardButton("✍️ Өзім жазамын"))
    await message.answer("\ud83d\udcde Телефон нөміріңізді жіберіңіз немесе жазыңыз:", reply_markup=contact_kb)
    await RequestForm.phone.set()

@dp.message_handler(content_types=types.ContentType.CONTACT, state=RequestForm.phone)
async def get_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("\ud83d\udcdc Сұрағыңызды сипаттап жазыңыз:", reply_markup=ReplyKeyboardRemove())
    await RequestForm.question.set()

@dp.message_handler(lambda message: message.text.startswith("✍️"), state=RequestForm.phone)
async def ask_manual_phone(message: types.Message):
    await message.answer("\ud83d\udcde Телефон нөміріңізді жазыңыз:")

@dp.message_handler(state=RequestForm.phone)
async def get_manual_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("\ud83d\udcdc Сұрағыңызды сипаттап жазыңыз:")
    await RequestForm.question.set()

@dp.message_handler(state=RequestForm.question)
async def get_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data['name']
    phone = data['phone']
    question = message.text

    # Отправка маме
    text = (
        f"\ud83d\udcc5 *Жаңа өтінім!*\n"
        f"\n\ud83d\udc64 Аты: {name}"
        f"\n\ud83d\udcde Телефон: {phone}"
        f"\n\ud83d\udcac Сұрақ: {question}"
        f"\n\n\ud83d\udcf1 WhatsApp: https://wa.me/{''.join(filter(str.isdigit, phone))}"
    )
    await bot.send_message(ADMIN_CHAT_ID, text, parse_mode="Markdown")
    await message.answer("\u0420\u0430\u049b\u043c\u0435\u0442! \u04e8\u0442\u0456\u043d\u0456\u04a3\u0456\u04a3\u0456\u0437 \u0436\u0456\u0431\u0435\u0440\u0456\u043b\u0434\u0456.", reply_markup=main_kb)
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
