import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

BOT_TOKEN = "8219073859:AAH2qL0-w9mQTxGOFNqv-svRALHFQ8MDorw"
ADMIN_ID = 1688416529
CHANNEL_ID = "@AutoHub62Channel"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилища объявлений
ads_data = {}
pending_ads = {}
editing_ads = {}

# -------------------- Стартовое меню --------------------
@dp.message(CommandStart())
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("🚗 Подать объявление", callback_data="add_ad")],
            [InlineKeyboardButton("📜 Правила", callback_data="rules")],
            [InlineKeyboardButton("👨‍💼 Связь с админом", url="https://t.me/saltrew")]
        ]
    )
    await message.answer(
        "👋 Здравствуйте!\nЯ бот AutoHub62.\nВыберите действие ниже ⬇️",
        reply_markup=keyboard
    )

# -------------------- Правила --------------------
@dp.callback_query(lambda c: c.data == "rules")
async def rules(callback: types.CallbackQuery):
    await callback.message.answer(
        "📜 *Правила размещения объявлений:*\n\n"
        "1. Авто должно быть в Рязани или области\n"
        "2. Цена реальная, например: 450.000 ₽\n"
        "3. Контакт обязателен\n"
        "4. Фото до 10 шт.\n"
        "5. Краткое описание приветствуется",
        parse_mode="Markdown"
    )

# -------------------- Начало подачи объявления --------------------
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(callback: types.CallbackQuery):
    ads_data[callback.from_user.id] = {"step": 1, "data": {}}
    await callback.message.answer("🚗 Введите марку и модель автомобиля:")

# -------------------- Обработка сообщений пользователя --------------------
@dp.message()
async def process_message(msg: types.Message):
    user_id = msg.from_user.id
    if user_id not in ads_data:
        return

    step_info = ads_data[user_id]
    step = step_info["step"]
    ad = step_info["data"]

    # Редактирование отдельных полей
    if isinstance(step, str) and step.startswith("edit_"):
        field = step.replace("edit_", "")
        ad[field] = msg.text
        await msg.answer(f"✅ Поле *{field}* обновлено. Можете редактировать другие поля или нажать 'Сохранить'.", parse_mode="Markdown")
        await send_preview_admin(user_id)
        del ads_data[user_id]
        return

    # -------------------- Шаги подачи объявления --------------------
    if step == 1:
        ad["model"] = msg.text
        ads_data[user_id]["step"] = 2
        await msg.answer("Введите год выпуска (только цифры, например 2015):")
    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("Введите только цифры для года выпуска.")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("Введите цену (например: 450.000 ₽):")
    elif step == 3:
        if not msg.text.replace(".", "").isdigit():
            await msg.answer("Введите только цифры для цены.")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("Введите пробег (км):")
    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("Введите только цифры для пробега.")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer("Отправьте фото автомобиля (до 10). Когда закончите, напишите 'стоп'.")
    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 6
                await msg.answer("Фото завершены. Введите контакт:")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer("Фото завершены. Введите контакт:")
        else:
            await msg.answer("Отправьте фото или напишите 'стоп'.")
    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer("Введите краткое описание автомобиля:")
    elif step == 7:
        ad["description"] = msg.text
        pending_ads[user_id] = ad

        text_preview = (
            f"📢 *Предварительный просмотр объявления*\n\n"
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📞 {ad['contact']}\n"
            f"📝 {ad['description']}"
        )

        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton("✅ Отправить на модерацию", callback_data=f"to_moderation_{user_id}")],
                [InlineKeyboardButton("✏️ Редактировать", callback_data=f"user_edit_{user_id}")],
                [InlineKeyboardButton("❌ Отменить объявление", callback_data=f"cancel_{user_id}")]
            ]
        )

        if media:
            await bot.send_media_group(chat_id=user_id, media=media)
        await bot.send_message(chat_id=user_id, text=text_preview, reply_markup=keyboard, parse_mode="Markdown")

        if user_id in ads_data:
            del ads_data[user_id]

# -------------------- Действия пользователя и модератора --------------------
@dp.callback_query(lambda c: c.data.startswith(("to_moderation_", "cancel_", "user_edit_")))
async def user_and_moderation(cq: types.CallbackQuery):
    data = cq.data
    user_id = int(data.split("_")[-1])

    # Отправка на модерацию
    if data.startswith("to_moderation_"):
        ad = pending_ads.get(user_id)
        if not ad:
            await cq.answer("Объявление не найдено.")
            return

        text_admin = (
            f"📝 *Новое объявление на модерацию*\n\n"
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📞 {ad['contact']}\n"
            f"📝 {ad['description']}"
        )

        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]

        keyboard_admin = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("✅ Опубликовать", callback_data=f"publish_{user_id}"),
                    InlineKeyboardButton("❌ Отклонить", callback_data=f"delete_{user_id}"),
                    InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_{user_id}")
                ]
            ]
        )

        editing_ads[user_id] = ad.copy()

        if media:
            await bot.send_media_group(chat_id=ADMIN_ID, media=media)
        await bot.send_message(chat_id=ADMIN_ID, text=text_admin, reply_markup=keyboard_admin, parse_mode="Markdown")
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление отправлено на модерацию!")

    # Отмена пользователем
    elif data.startswith("cancel_"):
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await bot.send_message(user_id, "Объявление отменено. Можете подать заново:",
                               reply_markup=InlineKeyboardMarkup(
                                   inline_keyboard=[[InlineKeyboardButton("🚗 Подать объявление", callback_data="add_ad")]]
                               ))
        await cq.answer()

    # Редактирование пользователем
    elif data.startswith("user_edit_"):
        ad = pending_ads.get(user_id)
        if not ad:
            await cq.answer("Объявление не найдено.")
            return
        editing_ads[user_id] = ad.copy()
        keyboard_fields = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton("🚗 Марка/Модель", callback_data=f"edit_field_model_{user_id}")],
                [InlineKeyboardButton("📅 Год", callback_data=f"edit_field_year_{user_id}")],
                [InlineKeyboardButton("💰 Цена", callback_data=f"edit_field_price_{user_id}")],
                [InlineKeyboardButton("📏 Пробег", callback_data=f"edit_field_mileage_{user_id}")],
                [InlineKeyboardButton("📞 Контакт", callback_data=f"edit_field_contact_{user_id}")],
                [InlineKeyboardButton("📝 Описание", callback_data=f"edit_field_description_{user_id}")],
                [InlineKeyboardButton("💾 Сохранить", callback_data=f"save_edit_{user_id}")],
                [InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_edit_{user_id}")]
            ]
        )
        await cq.message.answer("✏️ Выберите поле для редактирования:", reply_markup=keyboard_fields)
        await cq.answer()

# -------------------- Редактирование отдельных полей --------------------
@dp.callback_query(lambda c: c.data.startswith("edit_field_"))
async def edit_field_callback(cq: types.CallbackQuery):
    parts = cq.data.split("_")
    field = parts[2]
    user_id = int(parts[3])
    ad = editing_ads.get(user_id)
    if not ad:
        await cq.answer("Объявление не найдено.")
        return
    await cq.message.answer(f"✏️ Введите новое значение для поля *{field}*:", parse_mode="Markdown")
    ads_data[cq.from_user.id] = {"step": f"edit_{field}", "data": ad, "user_id": user_id}
    await cq.answer()

# -------------------- Сохранение редактирования --------------------
@dp.callback_query(lambda c: c.data.startswith(("save_edit_", "cancel_edit_")))
async def handle_edit_save(cq: types.CallbackQuery):
    user_id = int(cq.data.split("_")[2])
    if cq.data.startswith("save_edit_"):
        ad = editing_ads.pop(user_id)
        pending_ads[user_id] = ad
        await cq.message.edit_reply_markup()
        await cq.answer("Изменения сохранены. Объявление готово к публикации!")
    elif cq.data.startswith("cancel_edit_"):
        editing_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Редактирование отменено.")

# -------------------- Публикация/отклонение админом --------------------
@dp.callback_query(lambda c: c.data.startswith(("publish_", "delete_")))
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
        msg = await bot.send_message(chat_id=CHANNEL_ID, text=text)
        await bot.send_message(user_id, f"✅ Ваше объявление опубликовано: [Ссылка]({msg.link})", parse_mode="Markdown")
        del pending_ads[user_id]
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление опубликовано!")
    elif cq.data.startswith("delete_") and ad:
        del pending_ads[user_id]
        await bot.send_message(user_id, "❌ Ваше объявление отклонено модератором.")
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление удалено.")

# -------------------- Запуск бота --------------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
