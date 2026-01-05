import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

BOT_TOKEN = "8219073859:AAH2qL0-w9mQTxGOFNqv-svRALHFQ8MDorw"
ADMIN_ID = 1688416529
CHANNEL_ID = "@AutoHub62Channel"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Хранилища ---
ads_data = {}               # Для пошаговой подачи объявления пользователем
pending_ads = {}            # Для объявлений, ожидающих модерации
editing_ads = {}            # Для редактирования модератором
user_editing_ads = {}       # Для редактирования пользователем перед отправкой

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
        "1. Авто должно быть в Рязани или области\n"
        "2. Цена реальная, в формате например: 450.000 ₽\n"
        "3. Контакт обязателен, например: номер телефона или @username\n"
        "4. Фото автомобиля до 10 шт.\n"
        "5. Краткое описание приветствуется",
        parse_mode="Markdown"
    )

# --- Начало подачи объявления ---
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(callback: types.CallbackQuery):
    ads_data[callback.from_user.id] = {"step": 1, "data": {}}
    await callback.message.answer("🚗 Введите марку и модель автомобиля:")

# --- Пошаговая подача объявления ---
@dp.message(lambda msg: msg.from_user.id in ads_data)
async def process_new_ad(msg: types.Message):
    user_id = msg.from_user.id
    step = ads_data[user_id]["step"]
    ad = ads_data[user_id]["data"]

    if step == 1:
        ad["model"] = msg.text
        ads_data[user_id]["step"] = 2
        await msg.answer("Введите год выпуска (только цифры, например 2015):")
        return

    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("Пожалуйста, введите только цифры для года выпуска.")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("Введите цену (например: 450.000 ₽):")
        return

    elif step == 3:
        if not msg.text.replace(".", "").isdigit():
            await msg.answer("Пожалуйста, введите только цифры для цены.")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("Введите пробег (км, только цифры):")
        return

    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("Пожалуйста, введите только цифры для пробега.")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer("Отправьте фото автомобиля (до 10). Когда закончите, напишите 'стоп'.")
        return

    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            await msg.answer(f"Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            return
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer("Фото завершены. Введите контакт (например: номер телефона или @username):")
            return
        else:
            await msg.answer("Отправьте фото или напишите 'стоп'.")
            return

    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer("Введите краткое описание автомобиля (например: 'Авто в хорошем состоянии, один владелец'):")
        return

    elif step == 7:
        ad["description"] = msg.text
        pending_ads[user_id] = ad
        await send_user_preview(user_id)
        del ads_data[user_id]
        return

# --- Предпросмотр объявления пользователем с кнопкой редактирования ---
async def send_user_preview(user_id: int):
    ad = pending_ads[user_id]
    media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
    text_preview = (
        f"📢 *Предварительный просмотр объявления*\n\n"
        f"🚗 {ad['model']}\n"
        f"📅 {ad['year']}\n"
        f"💰 {ad['price']} ₽\n"
        f"📏 {ad['mileage']} км\n"
        f"📞 {ad['contact']}\n"
        f"📝 {ad['description']}"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("✏️ Редактировать", callback_data=f"user_edit_{user_id}")],
            [InlineKeyboardButton("✅ Отправить на модерацию", callback_data=f"to_moderation_{user_id}")],
            [InlineKeyboardButton("❌ Отменить объявление", callback_data=f"cancel_{user_id}")]
        ]
    )
    if media:
        await bot.send_media_group(chat_id=user_id, media=media)
    await bot.send_message(chat_id=user_id, text=text_preview, reply_markup=keyboard, parse_mode="Markdown")

# --- Обработка кнопок модерации и пользователя ---
@dp.callback_query(lambda c: c.data.startswith((
    "to_moderation_", "cancel_", "edit_", "user_edit_",
    "edit_field_", "save_edit_", "cancel_edit_")))
async def moderation_actions(cq: types.CallbackQuery):
    data = cq.data
    user_id = int(data.split("_")[-1])

    # --- Отправка на модерацию ---
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
        if media:
            await bot.send_media_group(chat_id=ADMIN_ID, media=media)
        await bot.send_message(chat_id=ADMIN_ID, text=text_admin, reply_markup=keyboard_admin, parse_mode="Markdown")
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление отправлено на модерацию!")

    # --- Отмена пользователем ---
    elif data.startswith("cancel_"):
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление отменено!")
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton("🚗 Подать объявление", callback_data="add_ad")]]
        )
        await bot.send_message(user_id, "Вы можете подать объявление заново:", reply_markup=keyboard)

    # --- Редактирование пользователем ---
    elif data.startswith("user_edit_"):
        ad = pending_ads[user_id]
        user_editing_ads[user_id] = {"data": ad.copy(), "field": None}
        keyboard_fields = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton("🚗 Марка/Модель", callback_data=f"user_edit_field_model_{user_id}")],
                [InlineKeyboardButton("📅 Год", callback_data=f"user_edit_field_year_{user_id}")],
                [InlineKeyboardButton("💰 Цена", callback_data=f"user_edit_field_price_{user_id}")],
                [InlineKeyboardButton("📏 Пробег", callback_data=f"user_edit_field_mileage_{user_id}")],
                [InlineKeyboardButton("📞 Контакт", callback_data=f"user_edit_field_contact_{user_id}")],
                [InlineKeyboardButton("📝 Описание", callback_data=f"user_edit_field_description_{user_id}")],
                [InlineKeyboardButton("❌ Отмена", callback_data=f"user_edit_cancel_{user_id}")]
            ]
        )
        await cq.message.answer("✏️ Выберите поле для редактирования:", reply_markup=keyboard_fields)
        await cq.answer()

# --- Выбор поля для редактирования пользователем ---
@dp.callback_query(lambda c: c.data.startswith("user_edit_field_"))
async def user_edit_field(cq: types.CallbackQuery):
    parts = cq.data.split("_")
    field = parts[3]
    user_id = int(parts[4])
    user_editing_ads[user_id]["field"] = field
    await cq.message.answer(f"✏️ Введите новое значение для поля *{field}*:", parse_mode="Markdown")
    await cq.answer()

# --- Обработка редактирования пользователем ---
@dp.message(lambda msg: msg.from_user.id in user_editing_ads and user_editing_ads[msg.from_user.id]["field"])
async def handle_user_field_edit(msg: types.Message):
    user_id = msg.from_user.id
    field = user_editing_ads[user_id]["field"]
    ad = user_editing_ads[user_id]["data"]
    ad[field] = msg.text
    user_editing_ads[user_id]["field"] = None
    pending_ads[user_id] = ad
    await msg.answer(f"Поле *{field}* обновлено.", parse_mode="Markdown")
    await send_user_preview(user_id)

# --- Запуск бота ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
