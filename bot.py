import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

BOT_TOKEN = "ВАШ_BOT_TOKEN"
ADMIN_ID = 1688416529
CHANNEL_ID = "@AutoHub62Channel"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

ads_data = {}        # Хранение текущего ввода пользователя
pending_ads = {}     # Хранение объявлений на модерацию

# --- Стартовое приветствие ---
@dp.message(CommandStart())
async def start(message: types.Message):
    if message.chat.type == "private":
        try:
            await message.delete()
        except:
            pass
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("🚗 Подать объявление", callback_data="add_ad")],
            [InlineKeyboardButton("📜 Правила", callback_data="rules")],
            [InlineKeyboardButton("👨‍💼 Связь с админом", url="https://t.me/saltrew")]
        ]
    )
    await message.answer(
        "👋 Здравствуйте!\n\n"
        "Я официальный бот канала **AutoHub62**.\n"
        "Помогаю удобно размещать объявления о продаже автомобилей.\n\n"
        "Выберите действие ниже ⬇️",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# --- Правила ---
@dp.callback_query(lambda c: c.data == "rules")
async def rules(callback: types.CallbackQuery):
    await callback.message.answer(
        "📜 *Правила размещения объявлений:*\n\n"
        "1. Все поля заполнены корректно\n"
        "2. Цена и пробег — цифрами\n"
        "3. Контакт доступен для связи\n"
        "4. Фото качественные\n"
        "5. Краткое описание информативное\n\n"
        "• Авто в Рязани или области\n"
        "• Реальная цена\n"
        "• Контакт обязателен",
        parse_mode="Markdown"
    )

# --- Начало подачи объявления ---
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    ads_data[user_id] = {"step": 1, "data": {}}
    await callback.message.answer(
        "🚗 *Шаг 1/7:* Введите марку и модель автомобиля.\n"
        "_Пример: Lada Vesta_",
        parse_mode="Markdown"
    )

# --- Обработка сообщений по шагам ---
@dp.message()
async def process_message(msg: types.Message):
    user_id = msg.from_user.id
    if user_id not in ads_data:
        return

    step = ads_data[user_id]["step"]
    ad = ads_data[user_id]["data"]

    # --- Шаги ---
    if step == 1:
        ad["model"] = msg.text
        ads_data[user_id]["step"] = 2
        await msg.answer("📅 *Шаг 2/7:* Введите год выпуска (только цифры). Пример: 2018", parse_mode="Markdown")
    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("⚠️ Введите только цифры для года выпуска.")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("💰 *Шаг 3/7:* Введите цену. Пример: 450.000", parse_mode="Markdown")
    elif step == 3:
        if not msg.text.replace(".", "").isdigit():
            await msg.answer("⚠️ Введите только цифры для цены.")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("📏 *Шаг 4/7:* Введите пробег в км. Пример: 50000", parse_mode="Markdown")
    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("⚠️ Введите только цифры для пробега.")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer("📷 *Шаг 5/7:* Отправьте фото автомобиля (до 10). Когда закончите, напишите 'стоп'.", parse_mode="Markdown")
    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"Фото принято ({len(ad['photos'])}/10). Можно прислать ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 6
                await msg.answer("Фото завершены. 📞 Введите контакт (номер или @username):")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer("Фото завершены. 📞 Введите контакт (номер или @username):")
        else:
            await msg.answer("Отправьте фото или напишите 'стоп'.")
    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer("📝 *Шаг 7/7:* Введите краткое описание автомобиля.\nПример: Отличное состояние, без ДТП.", parse_mode="Markdown")
    elif step == 7:
        ad["description"] = msg.text
        ads_data[user_id]["step"] = 8
        # Предпросмотр
        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
        text_preview = (
            f"📢 *Предпросмотр вашего объявления:*\n\n"
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📞 {ad['contact']}\n"
            f"📝 {ad['description']}"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton("✅ Отправить на модерацию", callback_data=f"sendmod_{user_id}")],
                [InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_{user_id}")]
            ]
        )
        if media:
            await bot.send_media_group(chat_id=msg.chat.id, media=media)
        await msg.answer(text_preview, parse_mode="Markdown", reply_markup=keyboard)

# --- Кнопки пользователя ---
@dp.callback_query(lambda c: c.data.startswith("sendmod_") or c.data.startswith("edit_"))
async def user_buttons(cq: types.CallbackQuery):
    user_id = int(cq.data.split("_")[1])
    ad = ads_data.get(user_id, {}).get("data")
    if cq.data.startswith("sendmod_"):
        if not ad:
            await cq.answer("Объявление не найдено.")
            return
        pending_ads[user_id] = ad
        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
        text_admin = (
            f"Новое объявление от {cq.from_user.full_name}:\n\n"
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📞 {ad['contact']}\n"
            f"📝 {ad['description']}"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton("✅ Опубликовать", callback_data=f"publish_{user_id}")],
                [InlineKeyboardButton("❌ Отклонить", callback_data=f"delete_{user_id}")],
                [InlineKeyboardButton("✏️ Редактировать", callback_data=f"admin_edit_{user_id}")]
            ]
        )
        if media:
            await bot.send_media_group(chat_id=ADMIN_ID, media=media)
        await bot.send_message(chat_id=ADMIN_ID, text=text_admin, reply_markup=keyboard)
        await cq.answer("Объявление отправлено на модерацию!")
        ads_data.pop(user_id, None)
    elif cq.data.startswith("edit_"):
        ads_data[user_id]["step"] = 1
        await cq.message.answer("✏️ Редактирование объявления. Снова введите марку и модель:")

# --- Кнопки админа ---
@dp.callback_query(lambda c: c.data.startswith("publish_") or c.data.startswith("delete_") or c.data.startswith("admin_edit_"))
async def admin_buttons(cq: types.CallbackQuery):
    if cq.from_user.id != ADMIN_ID:
        await cq.answer("Только админ может управлять объявлениями.")
        return
    user_id = int(cq.data.split("_")[1])
    ad = pending_ads.get(user_id)
    if not ad:
        await cq.answer("Объявление не найдено.")
        return
    if cq.data.startswith("publish_"):
        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
        text = (
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📞 {ad['contact']}\n"
            f"📝 {ad['description']}"
        )
        if media:
            await bot.send_media_group(chat_id=CHANNEL_ID, media=media)
        await bot.send_message(chat_id=CHANNEL_ID, text=text)
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление опубликовано!")
    elif cq.data.startswith("delete_"):
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление отклонено.")
    elif cq.data.startswith("admin_edit_"):
        ads_data[user_id] = {"step": 1, "data": ad.copy()}
        pending_ads.pop(user_id, None)
        await cq.message.answer("✏️ Редактирование админом. Снова введите марку и модель:")

# --- Запуск бота ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
