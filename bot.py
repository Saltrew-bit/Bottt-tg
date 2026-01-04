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
        "2. Цена реальная и корректная\n"
        "3. Контакт обязателен\n"
        "4. Фотографии автомобиля должны быть качественные\n"
        "5. Краткое описание авто\n\n"
        "⚠️ *Примеры ввода:*\n"
        "• Год выпуска: 2015\n"
        "• Цена: 450.000 ₽\n"
        "• Пробег: 120000 км\n"
        "• Контакт: +7 900 123-45-67 или @username",
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
        await msg.answer("Введите год выпуска (только цифры, например: 2015):")

    # Шаг 2: год
    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("Пожалуйста, введите только цифры для года выпуска.")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("Введите цену (например: 450.000):")

    # Шаг 3: цена
    elif step == 3:
        if not msg.text.replace(".", "").isdigit():
            await msg.answer("Пожалуйста, введите только цифры для цены.")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("Введите пробег в км (только цифры, например: 120000):")

    # Шаг 4: пробег
    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("Пожалуйста, введите только цифры для пробега.")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer("Отправьте фото автомобиля (до 10). Когда закончите, напишите 'стоп'.")

    # Шаг 5: фото
    elif step == 5:
        if msg.photo:
            # Берем последний вариант качества и сохраняем file_id
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 6
                await msg.answer("Фото завершены. Введите контакт (например: +7 900 123-45-67 или @username):")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer("Фото завершены. Введите контакт (например: +7 900 123-45-67 или @username):")
        else:
            await msg.answer("Отправьте фото или напишите 'стоп'.")

    # Шаг 6: контакт
    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer("Введите краткое описание автомобиля:")

    # Шаг 7: описание
    elif step == 7:
        ad["description"] = msg.text
        pending_ads[user_id] = ad

        text = (
            f"📢 *Новое объявление от {msg.from_user.full_name}:*\n\n"
            f"🚗 {ad['model']}\n"
            f"📅 Год: {ad['year']}\n"
            f"💰 Цена: {ad['price']} ₽\n"
            f"📏 Пробег: {ad['mileage']} км\n"
            f"📞 Контакт: {ad['contact']}\n"
            f"📝 Описание: {ad['description']}"
        )

        media_group = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Отправить на модерацию", callback_data=f"to_moderation_{user_id}"),
                    InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{user_id}")
                ]
            ]
        )

        if media_group:
            await bot.send_media_group(chat_id=msg.chat.id, media=media_group)

        await bot.send_message(chat_id=msg.chat.id, text=text, reply_markup=keyboard, parse_mode="Markdown")
        ads_data.pop(user_id)  # очищаем временные данные, пользователь закончил ввод

# --- Действия админа ---
@dp.callback_query(lambda c: c.data.startswith("to_moderation_") or c.data.startswith("cancel_"))
async def handle_admin_actions(cq: types.CallbackQuery):
    user_id = int(cq.data.split("_")[-1])
    if cq.data.startswith("to_moderation_"):
        ad = pending_ads.get(user_id)
        if ad:
            text = (
                f"🚨 *Объявление на модерацию:*\n\n"
                f"🚗 {ad['model']}\n"
                f"📅 Год: {ad['year']}\n"
                f"💰 Цена: {ad['price']} ₽\n"
                f"📏 Пробег: {ad['mileage']} км\n"
                f"📞 Контакт: {ad['contact']}\n"
                f"📝 Описание: {ad['description']}"
            )

            media_group = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"publish_{user_id}"),
                        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{user_id}"),
                        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"delete_{user_id}")
                    ]
                ]
            )

            if media_group:
                await bot.send_media_group(chat_id=ADMIN_ID, media=media_group)
            await bot.send_message(chat_id=ADMIN_ID, text=text, reply_markup=keyboard, parse_mode="Markdown")
            await cq.answer("Объявление отправлено на модерацию!")
        else:
            await cq.answer("Объявление не найдено.")

    elif cq.data.startswith("cancel_"):
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление отменено.")

# --- Публикация, редактирование и удаление ---
@dp.callback_query(lambda c: c.data.startswith(("publish_", "edit_", "delete_")))
async def admin_manage(cq: types.CallbackQuery):
    if cq.from_user.id != ADMIN_ID:
        await cq.answer("Только админ может управлять объявлениями.")
        return

    action, user_id = cq.data.split("_")[0], int(cq.data.split("_")[1])
    ad = pending_ads.get(user_id)

    if not ad:
        await cq.answer("Объявление не найдено.")
        return

    if action == "publish":
        media_group = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
        text = (
            f"🚗 {ad['model']}\n"
            f"📅 Год: {ad['year']}\n"
            f"💰 Цена: {ad['price']} ₽\n"
            f"📏 Пробег: {ad['mileage']} км\n"
            f"📞 Контакт: {ad['contact']}\n"
            f"📝 Описание: {ad['description']}"
        )
        if media_group:
            await bot.send_media_group(chat_id=CHANNEL_ID, media=media_group)
        await bot.send_message(chat_id=CHANNEL_ID, text=text)
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление опубликовано!")

    elif action == "delete":
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление удалено!")

    elif action == "edit":
        # Вернуть пользователю для редактирования
        ads_data[user_id] = {"step": 1, "data": ad.copy()}
        await cq.message.answer("✏️ Вы редактируете объявление. Введите новые данные по шагам, как раньше.")
        await cq.answer("Объявление возвращено пользователю для редактирования.")

# --- Запуск бота ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
