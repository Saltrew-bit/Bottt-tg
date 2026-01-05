import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

BOT_TOKEN = "ВАШ_ТОКЕН"
ADMIN_ID = 1688416529
CHANNEL_ID = "@AutoHub62Channel"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

ads_data = {}
pending_ads = {}
editing_ads = {}  # Для редактирования админом

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

# --- Обработка всех сообщений пользователя ---
@dp.message()
async def handle_messages(msg: types.Message):
    uid = msg.from_user.id

    # Если пользователь в процессе редактирования поля
    if uid in ads_data:
        step_info = ads_data[uid]
        step = step_info["step"]

        # --- Редактирование отдельного поля ---
        if isinstance(step, str) and step.startswith("edit_"):
            field = step.replace("edit_", "")
            ad = step_info["data"]
            ad[field] = msg.text
            await msg.answer(f"Поле *{field}* обновлено.", parse_mode="Markdown")
            if step_info.get("user_id"):  # если это редактирование админом
                await send_preview_admin(step_info["user_id"])
            del ads_data[uid]
            return

        # --- Продолжение обычного FSM подачи объявления ---
        ad = step_info["data"]

        if step == 1:
            ad["model"] = msg.text
            ads_data[uid]["step"] = 2
            await msg.answer("Введите год выпуска (только цифры, например 2015):")

        elif step == 2:
            if not msg.text.isdigit():
                await msg.answer("Введите только цифры для года выпуска.")
                return
            ad["year"] = msg.text
            ads_data[uid]["step"] = 3
            await msg.answer("Введите цену (например: 450.000 ₽):")

        elif step == 3:
            if not msg.text.replace(".", "").isdigit():
                await msg.answer("Введите только цифры для цены.")
                return
            ad["price"] = msg.text
            ads_data[uid]["step"] = 4
            await msg.answer("Введите пробег (км, только цифры):")

        elif step == 4:
            if not msg.text.isdigit():
                await msg.answer("Введите только цифры для пробега.")
                return
            ad["mileage"] = msg.text
            ads_data[uid]["step"] = 5
            await msg.answer("Отправьте фото автомобиля (до 10). Когда закончите, напишите 'стоп'.")

        elif step == 5:
            if msg.photo:
                ad.setdefault("photos", []).append(msg.photo[-1].file_id)
                await msg.answer(f"Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            elif msg.text.lower() == "стоп":
                ads_data[uid]["step"] = 6
                await msg.answer("Фото завершены. Введите контакт (например: номер телефона или @username):")
            else:
                await msg.answer("Отправьте фото или напишите 'стоп'.")

        elif step == 6:
            ad["contact"] = msg.text
            ads_data[uid]["step"] = 7
            await msg.answer("Введите краткое описание автомобиля:")

        elif step == 7:
            ad["description"] = msg.text
            pending_ads[uid] = ad

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("✅ Отправить на модерацию", callback_data=f"to_moderation_{uid}")],
                [InlineKeyboardButton("❌ Отменить объявление", callback_data=f"cancel_{uid}")]
            ])

            if ad.get("photos"):
                await bot.send_media_group(
                    uid,
                    [InputMediaPhoto(media=p) for p in ad["photos"]]
                )

            await bot.send_message(uid, "📢 *Предварительный просмотр объявления:*\n\n" + format_ad(ad),
                                   reply_markup=keyboard, parse_mode="Markdown")
            del ads_data[uid]

# --- Форматирование объявления ---
def format_ad(ad):
    return (
        f"🚗 {ad['model']}\n"
        f"📅 {ad['year']}\n"
        f"💰 {ad['price']} ₽\n"
        f"📏 {ad['mileage']} км\n"
        f"📞 {ad['contact']}\n"
        f"📝 {ad['description']}"
    )

# --- Действия модерации и редактирования ---
@dp.callback_query(lambda c: c.data.startswith(("to_moderation_", "cancel_", "edit_", "save_edit_", "cancel_edit_", "edit_field_")))
async def moderation_actions(cq: types.CallbackQuery):
    data = cq.data
    uid = int(data.split("_")[-1])

    # --- Отправка на модерацию ---
    if data.startswith("to_moderation_"):
        ad = pending_ads.get(uid)
        if not ad:
            await cq.answer("Объявление не найдено.")
            return

        keyboard_admin = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton("✅ Опубликовать", callback_data=f"publish_{uid}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"delete_{uid}"),
                InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_{uid}")
            ]
        ])

        if ad.get("photos"):
            await bot.send_media_group(ADMIN_ID, [InputMediaPhoto(media=p) for p in ad["photos"]])

        await bot.send_message(ADMIN_ID, "📝 *Новое объявление на модерацию*\n\n" + format_ad(ad),
                               reply_markup=keyboard_admin, parse_mode="Markdown")
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление отправлено на модерацию!")

    # --- Отмена объявления пользователем ---
    elif data.startswith("cancel_"):
        pending_ads.pop(uid, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление отменено!")
        await bot.send_message(uid, "Вы можете подать объявление заново:",
                               reply_markup=InlineKeyboardMarkup(
                                   inline_keyboard=[[InlineKeyboardButton("🚗 Подать объявление", callback_data="add_ad")]]
                               ))

    # --- Редактирование админом ---
    elif data.startswith("edit_"):
        ad = pending_ads.get(uid)
        if not ad:
            await cq.answer("Объявление не найдено.")
            return
        editing_ads[uid] = ad.copy()
        keyboard_fields = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("🚗 Марка/Модель", callback_data=f"edit_field_model_{uid}")],
            [InlineKeyboardButton("📅 Год", callback_data=f"edit_field_year_{uid}")],
            [InlineKeyboardButton("💰 Цена", callback_data=f"edit_field_price_{uid}")],
            [InlineKeyboardButton("📏 Пробег", callback_data=f"edit_field_mileage_{uid}")],
            [InlineKeyboardButton("📞 Контакт", callback_data=f"edit_field_contact_{uid}")],
            [InlineKeyboardButton("📝 Описание", callback_data=f"edit_field_description_{uid}")],
            [InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_edit_{uid}")]
        ])
        await cq.message.answer("✏️ Выберите поле для редактирования:", reply_markup=keyboard_fields)
        await cq.answer()

    # --- Редактирование конкретного поля ---
    elif data.startswith("edit_field_"):
        parts = data.split("_")
        field = parts[2]
        ad = editing_ads.get(uid)
        if not ad:
            await cq.answer("Объявление не найдено.")
            return
        await cq.message.answer(f"✏️ Введите новое значение для поля *{field}*:", parse_mode="Markdown")
        ads_data[cq.from_user.id] = {"step": f"edit_{field}", "data": ad, "user_id": uid}
        await cq.answer()

    # --- Сохранение редактирования ---
    elif data.startswith("save_edit_"):
        ad = editing_ads.pop(uid)
        pending_ads[uid] = ad
        await cq.message.edit_reply_markup()
        await cq.answer("Изменения сохранены! Объявление готово к публикации.")

    elif data.startswith("cancel_edit_"):
        editing_ads.pop(uid, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Редактирование отменено.")

# --- Публикация/удаление админом ---
@dp.callback_query(lambda c: c.data.startswith(("publish_", "delete_")))
async def handle_admin_actions(cq: types.CallbackQuery):
    if cq.from_user.id != ADMIN_ID:
        await cq.answer("Только админ может управлять объявлениями.")
        return
    uid = int(cq.data.split("_")[1])

    if cq.data.startswith("publish_"):
        ad = pending_ads.get(uid)
        if ad:
            media = [InputMediaPhoto(media=p) for p in ad.get("photos", [])]
            if media:
                await bot.send_media_group(CHANNEL_ID, media)
            await bot.send_message(CHANNEL_ID, format_ad(ad))
            del pending_ads[uid]
            await cq.message.edit_reply_markup()
            await cq.answer("Объявление опубликовано!")
        else:
            await cq.answer("Объявление не найдено.")
    elif cq.data.startswith("delete_"):
        pending_ads.pop(uid, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление удалено.")

# --- Запуск бота ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
