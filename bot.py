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
        "2. Цена должна быть реальной и указанной цифрами\n"
        "3. Контакт обязателен (номер телефона или @username)\n"
        "4. Подробное описание приветствуется\n"
        "5. Фото должны соответствовать реальному автомобилю",
        parse_mode="Markdown"
    )

# --- Начало подачи объявления ---
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(callback: types.CallbackQuery):
    ads_data[callback.from_user.id] = {"step": 1, "data": {}}
    await callback.message.answer("🚗 Введите марку и модель автомобиля:")

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
        await msg.answer("📅 Введите год выпуска (только цифры, например: 2015):")

    # Шаг 2: год
    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("⚠️ Пожалуйста, введите только цифры для года выпуска.")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("💰 Введите цену (например: 450.000):")

    # Шаг 3: цена
    elif step == 3:
        if not msg.text.replace(".", "").isdigit():
            await msg.answer("⚠️ Пожалуйста, введите только цифры для цены.")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("📏 Введите пробег (км, только цифры):")

    # Шаг 4: пробег
    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("⚠️ Пожалуйста, введите только цифры для пробега.")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer("📸 Отправьте фото автомобиля (до 10). Когда закончите, напишите 'стоп'.")

    # Шаг 5: фото
    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 6
                await msg.answer("Фото завершены. Введите контакт (номер телефона или @username):")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer("Фото завершены. Введите контакт (номер телефона или @username):")
        else:
            await msg.answer("⚠️ Отправьте фото или напишите 'стоп'.")

    # Шаг 6: контакт
    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer("📝 Введите краткое описание автомобиля:")

    # Шаг 7: описание + предпросмотр
    elif step == 7:
        ad["description"] = msg.text

        # Предпросмотр текста
        preview_text = (
            f"📋 *Предпросмотр вашего объявления:*\n\n"
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📞 {ad['contact']}\n"
            f"📝 {ad['description']}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton("🛠 Отправить на модерацию", callback_data=f"send_for_review_{user_id}")],
                [InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{user_id}")]
            ]
        )

        # Отправляем предпросмотр текста с кнопками
        await msg.answer(preview_text, reply_markup=keyboard, parse_mode="Markdown")

        # Если есть фото, отправляем их отдельно
        if "photos" in ad and ad["photos"]:
            asyncio.create_task(send_user_photos(user_id, ad["photos"]))

        ads_data.pop(user_id, None)

# --- Асинхронная отправка фото пользователю ---
async def send_user_photos(user_id, photo_ids):
    media = [InputMediaPhoto(media=pid) for pid in photo_ids]
    await bot.send_media_group(chat_id=user_id, media=media)

# --- Действия админа и модерация ---
@dp.callback_query(lambda c: c.data.startswith("send_for_review_") or c.data.startswith("cancel_") 
                   or c.data.startswith("publish_") or c.data.startswith("delete_"))
async def handle_admin_actions(cq: types.CallbackQuery):
    user_id = int(cq.data.split("_")[-1])

    # Пользовательская модерация
    if cq.data.startswith("send_for_review_"):
        ad = ads_data.get(user_id) or pending_ads.get(user_id)
        if ad:
            pending_ads[user_id] = ad
            text = (
                f"Новое объявление от {cq.from_user.full_name}:\n\n"
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
            await bot.send_message(chat_id=ADMIN_ID, text=text)
            await cq.answer("✅ Ваше объявление отправлено на модерацию!")
        else:
            await cq.answer("❌ Объявление не найдено.")

    elif cq.data.startswith("cancel_"):
        ads_data.pop(user_id, None)
        pending_ads.pop(user_id, None)
        await cq.answer("❌ Отправка объявления отменена.")

    # Действия админа
    elif cq.from_user.id == ADMIN_ID:
        if cq.data.startswith("publish_"):
            ad = pending_ads.get(user_id)
            if ad:
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
                await cq.answer("✅ Объявление опубликовано!")
            else:
                await cq.answer("❌ Объявление не найдено.")
        elif cq.data.startswith("delete_"):
            pending_ads.pop(user_id, None)
            await cq.message.edit_reply_markup()
            await cq.answer("❌ Объявление удалено.")

# --- Запуск бота ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
