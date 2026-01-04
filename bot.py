import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

BOT_TOKEN = "8219073859:AAH2qL0-w9mQTxGOFNqv-svRALHFQ8MDorw"
ADMIN_ID = 1688416529
CHANNEL_ID = "@AutoHub62Channel"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

ads_data = {}       # Для пользователей, которые создают объявление
pending_ads = {}    # Для объявлений на модерации

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
        "1. Авто в Рязани или области\n"
        "2. Реальная цена\n"
        "3. Контакт обязателен\n"
        "4. Четкое описание и фотографии\n"
        "5. Корректные данные о годе выпуска, пробеге и цене",
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

    # --- Шаг 1: марка и модель ---
    if step == 1:
        ad["model"] = msg.text
        ads_data[user_id]["step"] = 2
        await msg.answer("📅 Введите год выпуска (только цифры, например: 2015):")

    # --- Шаг 2: год ---
    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("⚠️ Пожалуйста, введите только цифры для года выпуска.")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("💰 Введите цену (только цифры, например: 450.000):")

    # --- Шаг 3: цена ---
    elif step == 3:
        if not msg.text.replace(".", "").isdigit():
            await msg.answer("⚠️ Пожалуйста, введите только цифры для цены.")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("📏 Введите пробег в км (только цифры):")

    # --- Шаг 4: пробег ---
    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("⚠️ Пожалуйста, введите только цифры для пробега.")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer("📸 Отправьте фото автомобиля (до 10). Когда закончите, напишите 'стоп'.")

    # --- Шаг 5: фото ---
    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 6
                await msg.answer("Фото завершены. Введите контакт (например: номер телефона или @username):")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer("Фото завершены. Введите контакт (например: номер телефона или @username):")
        else:
            await msg.answer("⚠️ Отправьте фото или напишите 'стоп'.")

    # --- Шаг 6: контакт ---
    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer("📝 Введите краткое описание автомобиля:")

    # --- Шаг 7: описание ---
    elif step == 7:
        ad["description"] = msg.text
        pending_ads[user_id] = ad

        # --- Предпросмотр объявления ---
        text_preview = (
            f"📌 *Предпросмотр вашего объявления:*\n\n"
            f"🚗 Марка и модель: {ad['model']}\n"
            f"📅 Год: {ad['year']}\n"
            f"💰 Цена: {ad['price']} ₽\n"
            f"📏 Пробег: {ad['mileage']} км\n"
            f"📞 Контакт: {ad['contact']}\n"
            f"📝 Описание: {ad['description']}\n\n"
            f"Если всё верно, отправьте на модерацию."
        )

        media_group = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]

        keyboard_user = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton("✅ Отправить на модерацию", callback_data=f"user_submit_{user_id}")],
                [InlineKeyboardButton("✏️ Редактировать", callback_data=f"user_edit_{user_id}")]
            ]
        )

        if media_group:
            await bot.send_media_group(chat_id=user_id, media=media_group)
        await bot.send_message(chat_id=user_id, text=text_preview, reply_markup=keyboard_user, parse_mode="Markdown")

        ads_data[user_id]["step"] = 8  # шаг подтверждения

# --- Обработка кнопок пользователя (предосмотр) ---
@dp.callback_query(lambda c: c.data.startswith("user_submit_") or c.data.startswith("user_edit_"))
async def handle_user_preview(cq: types.CallbackQuery):
    user_id = int(cq.data.split("_")[-1])
    ad = ads_data.get(user_id, {}).get("data") or pending_ads.get(user_id)
    if not ad:
        await cq.answer("Объявление не найдено.")
        return

    if cq.data.startswith("user_submit_"):
        # Отправка админу на модерацию
        text_admin = (
            f"📢 *Новое объявление для модерации:*\n\n"
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📞 {ad['contact']}\n"
            f"📝 {ad['description']}"
        )
        media_admin = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
        keyboard_admin = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("✅ Опубликовать", callback_data=f"publish_{user_id}"),
                    InlineKeyboardButton("❌ Отклонить", callback_data=f"delete_{user_id}"),
                    InlineKeyboardButton("✏️ Редактировать", callback_data=f"admin_edit_{user_id}")
                ]
            ]
        )
        if media_admin:
            await bot.send_media_group(chat_id=ADMIN_ID, media=media_admin)
        await bot.send_message(chat_id=ADMIN_ID, text=text_admin, reply_markup=keyboard_admin, parse_mode="Markdown")
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление отправлено на модерацию!")
        if user_id in ads_data:
            del ads_data[user_id]

    elif cq.data.startswith("user_edit_"):
        ads_data[user_id]["step"] = 1
        await cq.message.answer("✏️ Давайте начнем редактирование объявления с шага 1. Введите марку и модель автомобиля:")
        await cq.answer()

# --- Действия админа ---
@dp.callback_query(lambda c: c.data.startswith("publish_") or c.data.startswith("delete_") or c.data.startswith("admin_edit_"))
async def handle_admin_actions(cq: types.CallbackQuery):
    if cq.from_user.id != ADMIN_ID:
        await cq.answer("Только админ может управлять объявлениями.")
        return

    data = cq.data
    user_id = int(data.split("_")[1])
    ad = pending_ads.get(user_id)
    if not ad:
        await cq.answer("Объявление не найдено.")
        return

    if data.startswith("publish_"):
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
        del pending_ads[user_id]
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление опубликовано!")

    elif data.startswith("delete_"):
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление удалено.")

    elif data.startswith("admin_edit_"):
        ads_data[user_id] = {"step": 1, "data": ad.copy()}
        await cq.message.answer("✏️ Админ начал редактирование. Введите марку и модель автомобиля:")
        await cq.answer()

# --- Запуск бота ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
