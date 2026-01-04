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
        "1. Авто должно быть в Рязани или области\n"
        "2. Указывайте реальную цену (например: 450.000 ₽)\n"
        "3. Контакт обязателен (номер или @username)\n"
        "4. Подробное описание автомобиля приветствуется\n"
        "5. Фото автомобиля (1-10 штук)\n\n"
        "Соблюдайте эти правила, чтобы объявление прошло модерацию.",
        parse_mode="Markdown"
    )

# --- Начало подачи объявления ---
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(callback: types.CallbackQuery):
    ads_data[callback.from_user.id] = {"step": 1, "data": {}}
    await callback.message.answer("🚗 Введите марку и модель автомобиля:\n*Пример:* Toyota Camry", parse_mode="Markdown")

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
        await msg.answer("📅 Введите год выпуска (только цифры):\n*Пример:* 2015", parse_mode="Markdown")
        return

    # Шаг 2: год
    if step == 2:
        if not msg.text.isdigit():
            await msg.answer("❌ Пожалуйста, введите только цифры для года выпуска.")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("💰 Введите цену (только цифры, можно с точкой для тысяч):\n*Пример:* 450.000", parse_mode="Markdown")
        return

    # Шаг 3: цена
    if step == 3:
        if not msg.text.replace(".", "").isdigit():
            await msg.answer("❌ Пожалуйста, введите только цифры для цены.")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("📏 Введите пробег (км, только цифры):\n*Пример:* 120000", parse_mode="Markdown")
        return

    # Шаг 4: пробег
    if step == 4:
        if not msg.text.isdigit():
            await msg.answer("❌ Пожалуйста, введите только цифры для пробега.")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer("📸 Отправьте фото автомобиля (до 10). Когда закончите, напишите 'стоп'.")
        return

    # Шаг 5: фото
    if step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 6
                await msg.answer("✅ Фото завершены. Введите контакт (номер или @username):\n*Пример:* +7 900 123-45-67", parse_mode="Markdown")
            return
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer("✅ Фото завершены. Введите контакт (номер или @username):\n*Пример:* +7 900 123-45-67", parse_mode="Markdown")
            return
        else:
            await msg.answer("❌ Отправьте фото или напишите 'стоп'.")
            return

    # Шаг 6: контакт
    if step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer("📝 Введите краткое описание автомобиля:\n*Пример:* Отличное состояние, один владелец, без ДТП.", parse_mode="Markdown")
        return

    # Шаг 7: описание
    if step == 7:
        ad["description"] = msg.text
        pending_ads[user_id] = ad
        ads_data.pop(user_id, None)

        # Подготовка предпросмотра
        text = (
            f"📣 *Предпросмотр вашего объявления:*\n\n"
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📞 {ad['contact']}\n"
            f"📝 {ad['description']}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Отправить на модерацию", callback_data=f"submit_{user_id}"),
                    InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{user_id}")
                ],
                [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{user_id}")]
            ]
        )

        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
        if media:
            await bot.send_media_group(chat_id=msg.chat.id, media=media)
        await msg.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        return

# --- Действия с предпросмотром ---
@dp.callback_query(lambda c: c.data.startswith(("submit_", "edit_", "cancel_")))
async def handle_preview(cq: types.CallbackQuery):
    user_id = int(cq.data.split("_")[1])
    ad = pending_ads.get(user_id)
    if not ad:
        await cq.answer("Объявление не найдено.")
        return

    if cq.data.startswith("submit_"):
        # Отправляем админу на модерацию
        text = (
            f"📌 *Новое объявление на модерацию:*\n\n"
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📞 {ad['contact']}\n"
            f"📝 {ad['description']}"
        )
        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
        if media:
            await bot.send_media_group(chat_id=ADMIN_ID, media=media)
        await bot.send_message(chat_id=ADMIN_ID, text=text, reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton("✅ Опубликовать", callback_data=f"publish_{user_id}")],
                [InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{user_id}")]
            ]
        ), parse_mode="Markdown")
        await cq.answer("Объявление отправлено на модерацию.")
        return

    if cq.data.startswith("edit_"):
        ads_data[user_id] = {"step": 1, "data": ad.copy()}
        pending_ads.pop(user_id, None)
        await cq.message.answer("✏️ Редактирование объявления. Начнем заново с марки и модели.")
        await cq.answer()
        return

    if cq.data.startswith("cancel_"):
        pending_ads.pop(user_id, None)
        await cq.message.answer("❌ Размещение объявления отменено.")
        await cq.answer()
        return

# --- Действия админа ---
@dp.callback_query(lambda c: c.data.startswith("publish_") or c.data.startswith("delete_"))
async def handle_admin_actions(cq: types.CallbackQuery):
    if cq.from_user.id != ADMIN_ID:
        await cq.answer("Только админ может управлять объявлениями.")
        return

    user_id = int(cq.data.split("_")[1])
    ad = pending_ads.get(user_id)
    if cq.data.startswith("publish_") and ad:
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
        return

    if cq.data.startswith("delete_"):
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление удалено.")
        return

# --- Запуск бота ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
