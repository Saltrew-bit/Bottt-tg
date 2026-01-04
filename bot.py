import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

BOT_TOKEN = "8219073859:AAH2qL0-w9mQTxGOFNqv-svRALHFQ8MDorw"
ADMIN_ID = 1688416529  # твой Telegram ID для модерации
CHANNEL_ID = "@AutoHub62Channel"  # канал для публикации

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_states = {}      # хранит состояние пользователей, которые подают объявления
pending_ads = {}      # объявления, ожидающие модерации

# ===== /start =====
@dp.message(CommandStart())
async def start(message: types.Message):
    if message.chat.type == "private":
        try:
            await message.delete()
        except Exception:
            pass

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🚗 Подать объявление", callback_data="add_ad")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules")],
        [InlineKeyboardButton("👨‍💼 Связь с админом", url="https://t.me/saltrew")]
    ])

    await message.answer(
        "👋 Здравствуйте!\n\n"
        "Я официальный бот канала **AutoHub62**.\n"
        "Помогаю удобно размещать объявления о продаже автомобилей.\n\n"
        "Выберите действие ниже ⬇️",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ===== Правила =====
@dp.callback_query(lambda c: c.data == "rules")
async def rules(callback: types.CallbackQuery):
    await callback.message.answer(
        "📜 *Правила размещения объявлений:*\n\n"
        "• Авто в Рязани или области\n"
        "• Реальная цена\n"
        "• Контакт обязателен",
        parse_mode="Markdown"
    )

# ===== Начало подачи объявления =====
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id] = {"step": 1, "data": {}}
    await callback.message.answer("🚗 Введите марку и модель автомобиля:")

# ===== Пошаговая обработка сообщений пользователя =====
@dp.message()
async def process_ad(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id]
    step = state["step"]
    ad = state["data"]

    if step == 1:
        ad["model"] = message.text
        state["step"] = 2
        await message.answer("Введите год выпуска:")
    elif step == 2:
        ad["year"] = message.text
        state["step"] = 3
        await message.answer("Введите цену (₽):")
    elif step == 3:
        ad["price"] = message.text
        state["step"] = 4
        await message.answer("Введите пробег (км):")
    elif step == 4:
        ad["mileage"] = message.text
        state["step"] = 5
        await message.answer(
            "Отправьте фото автомобиля (до 10 шт.).\n"
            "Когда закончите, напишите 'стоп'."
        )
    elif step == 5:
        if message.photo:
            ad.setdefault("photos", []).append(message.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await message.answer(f"Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            else:
                state["step"] = 6
                await message.answer("Фото завершены. Введите описание автомобиля:")
        elif message.text.lower() == "стоп":
            state["step"] = 6
            await message.answer("Фото завершены. Введите описание автомобиля:")
        else:
            await message.answer("Отправьте фото или напишите 'стоп'.")
    elif step == 6:
        ad["description"] = message.text
        state["step"] = 7
        await message.answer("Введите контакт для связи (телефон/Telegram):")
    elif step == 7:
        ad["contact"] = message.text
        pending_ads[user_id] = ad
        del user_states[user_id]

        text = (
            f"Новое объявление от {message.from_user.full_name}:\n\n"
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📝 {ad['description']}\n"
            f"📞 {ad['contact']}"
        )

        media = [types.InputMediaPhoto(pid) for pid in ad.get("photos", [])]
        if media:
            await bot.send_media_group(ADMIN_ID, media)
        await bot.send_message(
            ADMIN_ID,
            text,
