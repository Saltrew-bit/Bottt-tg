import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

BOT_TOKEN = "8219073859:AAH2qL0-w9mQTxGOFNqv-svRALHFQ8MDorw"
ADMIN_ID = 1688416529
CHANNEL_ID = "@AutoHub62Channel"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

ads_data = {}
pending_ads = {}

# --- Вспомогательная функция для красивого оформления ---
def step_card(title, content, example=None, warning=None, emoji="📌"):
    msg = f"{emoji} {title}\n{content}"
    if example:
        msg += f"\n💡 Пример: {example}"
    if warning:
        msg += f"\n❌ {warning}"
    return msg

# --- Стартовое приветствие ---
@dp.message(CommandStart())
async def start(message: types.Message):
    if message.chat.type == "private":
        try:
            await message.delete()
        except Exception:
            pass

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚗 Подать объявление", callback_data="add_ad")],
            [InlineKeyboardButton(text="📜 Правила", callback_data="rules")],
            [InlineKeyboardButton(text="👨‍💼 Связь с админом", url="https://t.me/saltrew")]
        ]
    )

    await message.answer(
        "👋 Здравствуйте!\n\n"
        "Я официальный бот канала AutoHub62.\n"
        "Помогаю удобно размещать объявления о продаже автомобилей.\n\n"
        "Выберите действие ниже ⬇️",
        reply_markup=keyboard
    )

# --- Правила ---
@dp.callback_query(lambda c: c.data == "rules")
async def rules(callback: types.CallbackQuery):
    await callback.message.answer(
        "📜 Правила размещения объявлений:\n\n"
        "1. Все данные должны быть корректными.\n"
        "2. Фото автомобиля обязательны.\n"
        "3. Цена должна быть реальной.\n"
        "4. Контакт обязателен.\n"
        "5. Описание автомобиля краткое, но информативное.\n"
        "• Авто в Рязани или области"
    )

# --- Начало подачи объявления ---
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(callback: types.CallbackQuery):
    ads_data[callback.from_user.id] = {"step": 1, "data": {}}
    await callback.message.answer(step_card("Шаг 1: Марка и модель", "Введите марку и модель автомобиля", example="Toyota Camry", emoji="🚗"))

# --- Обработка сообщений по шагам ---
@dp.message()
async def process_message(msg: types.Message):
    user_id = msg.from_user.id
    if user_id not in ads_data:
        return

    step = ads_data[user_id]["step"]
    ad = ads_data[user_id]["data"]

    # Шаг 1: марка и модель
    if step == 1:
        ad["model"] = msg.text
        ads_data[user_id]["step"] = 2
        await msg.answer(step_card("Шаг 2: Год выпуска", "Введите год автомобиля", example="2015", warning="Только цифры", emoji="📅"))

    # Шаг 2: год
    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("❌ Пожалуйста, введите только цифры для года выпуска.")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer(step_card("Шаг 3: Цена", "Введите цену автомобиля", example="450.000", warning="Только цифры", emoji="💰"))

    # Шаг 3: цена
    elif step == 3:
        if not msg.text.replace(".", "").isdigit():
            await msg.answer("❌ Пожалуйста, введите только цифры для цены.")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer(step_card("Шаг 4: Пробег", "Введите пробег автомобиля в км", example="120000", warning="Только цифры", emoji="📏"))

    # Шаг 4: пробег
    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("❌ Пожалуйста, введите только цифры для пробега.")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer(step_card("Шаг 5: Фото", "Отправьте фото автомобиля (до 10). Когда закончите, напишите 'стоп'.", emoji="📸"))

    # Шаг 5: фото
    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 6
                await msg.answer(step_card("Шаг 6: Контакт", "Введите контакт (телефон или Telegram)", example="@username / +79001234567", emoji="📞"))
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer(step_card("Шаг 6: Контакт", "Введите контакт (телефон или Telegram)", example="@username / +79001234567", emoji="📞"))
        else:
            await msg.answer("❌ Отправьте фото или напишите 'стоп'.")

    # Шаг 6: контакт
    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer(step_card("Шаг 7: Краткое описание автомобиля", "Введите описание автомобиля", example="Отличное состояние, не битый", emoji="📝"))

    # Шаг 7: описание
    elif step == 7:
        ad["description"] = msg.text
        pending_ads[user_id] = ad

        # Предпросмотр объявления
        text_preview = (
            f"📋 Предпросмотр объявления\n\n"
            f"🚗 Модель: {ad['model']}\n"
            f"📅 Год: {ad['year']}\n"
            f"💰 Цена: {ad['price']} ₽\n"
            f"📏 Пробег: {ad['mileage']} км\n"
            f"📞 Контакт: {ad['contact']}\n"
            f"📝 Описание: {ad['description']}\n\n"
            f"После проверки администратором объявление будет опубликовано в канале."
        )

        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Отправить на модерацию", callback_data=f"moderate_{user_id}")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{user_id}")]
            ]
        )

        if media:
            await bot.send_media_group(chat_id=ADMIN_ID, media=media)

        await bot.send_message(chat_id=ADMIN_ID, text=text_preview, reply_markup=keyboard)
        await msg.answer("Объявление принято и отправлено на модерацию. Спасибо!")
        del ads_data[user_id]

# --- Модерация админом ---
@dp.callback_query(lambda c: c.data.startswith("moderate_") or c.data.startswith("cancel_"))
async def handle_admin(cq: types.CallbackQuery):
    if cq.from_user.id != ADMIN_ID:
        await cq.answer("Только админ может управлять объявлениями.")
        return

    data = cq.data
    user_id = int(data.split("_")[1])
    ad = pending_ads.get(user_id)

    if data.startswith("moderate_") and ad:
        text = (
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📞 {ad['contact']}\n"
            f"📝 {ad['description']}"
        )
        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
        if media:
            await bot.send_media_group(chat_id=CHANNEL_ID, media=media)
        await bot.send_message(chat_id=CHANNEL_ID, text=text)
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление опубликовано!")
    elif data.startswith("cancel_"):
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление отменено.")

# --- Запуск бота ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
