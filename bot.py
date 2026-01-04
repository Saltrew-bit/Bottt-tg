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
        "1. Заголовок и описание должны быть информативными и точными.\n"
        "2. Указывайте правильный год выпуска, пробег и цену.\n"
        "3. Фото автомобиля должны быть качественными.\n"
        "4. Контакт обязателен (номер телефона или @username).\n"
        "5. Объявление проверяется модератором перед публикацией.",
        parse_mode="Markdown"
    )

# --- Начало подачи объявления ---
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(callback: types.CallbackQuery):
    ads_data[callback.from_user.id] = {"step": 1, "data": {}}
    await callback.message.answer(
        "🚗 *Шаг 1/7*: Введите марку и модель автомобиля.\n"
        "_Пример: Toyota Camry_",
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

    # Шаг 1: марка и модель
    if step == 1:
        ad["model"] = msg.text
        ads_data[user_id]["step"] = 2
        await msg.answer(
            "📅 *Шаг 2/7*: Введите год выпуска (только цифры).\n"
            "_Пример: 2018_",
            parse_mode="Markdown"
        )

    # Шаг 2: год
    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("⚠️ Пожалуйста, введите только цифры для года выпуска.")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer(
            "💰 *Шаг 3/7*: Введите цену (только цифры).\n"
            "_Пример: 450000_",
            parse_mode="Markdown"
        )

    # Шаг 3: цена
    elif step == 3:
        if not msg.text.replace(".", "").isdigit():
            await msg.answer("⚠️ Пожалуйста, введите только цифры для цены.")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer(
            "📏 *Шаг 4/7*: Введите пробег (км, только цифры).\n"
            "_Пример: 75000_",
            parse_mode="Markdown"
        )

    # Шаг 4: пробег
    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("⚠️ Пожалуйста, введите только цифры для пробега.")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer(
            "📸 *Шаг 5/7*: Отправьте фото автомобиля (до 10).\n"
            "_Когда закончите, напишите 'стоп'._",
            parse_mode="Markdown"
        )

    # Шаг 5: фото
    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"✅ Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 6
                await msg.answer(
                    "📞 *Шаг 6/7*: Фото завершены. Введите контакт.\n"
                    "_Пример: 8-999-123-45-67 или @username_",
                    parse_mode="Markdown"
                )
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer(
                "📞 *Шаг 6/7*: Фото завершены. Введите контакт.\n"
                "_Пример: 8-999-123-45-67 или @username_",
                parse_mode="Markdown"
            )
        else:
            await msg.answer("⚠️ Отправьте фото или напишите 'стоп'.")

    # Шаг 6: контакт
    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer(
            "📝 *Шаг 7/7*: Введите краткое описание автомобиля.\n"
            "_Пример: Отличное состояние, без ДТП, все ТО пройдены, 2 владельца._",
            parse_mode="Markdown"
        )

    # Шаг 7: описание и предпросмотр
    elif step == 7:
        ad["description"] = msg.text
        ads_data[user_id]["step"] = 8  # шаг предпросмотра
        pending_ads[user_id] = ad

        text_preview = (
            f"📢 *Предпросмотр вашего объявления:*\n\n"
            f"🚗 *Модель:* {ad['model']}\n"
            f"📅 *Год выпуска:* {ad['year']}\n"
            f"💰 *Цена:* {ad['price']} ₽\n"
            f"📏 *Пробег:* {ad['mileage']} км\n"
            f"📞 *Контакт:* {ad['contact']}\n"
            f"📝 *Описание:* {ad['description']}\n\n"
            f"Если всё верно, нажмите ✅ 'Отправить на модерацию',\n"
            f"или ❌ 'Отменить', чтобы переделать объявление."
        )

        keyboard_preview = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton("✅ Отправить на модерацию", callback_data=f"sendmod_{user_id}")],
                [InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{user_id}")]
            ]
        )

        media_preview = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
        if media_preview:
            await bot.send_media_group(chat_id=user_id, media=media_preview)

        await bot.send_message(
            chat_id=user_id,
            text=text_preview,
            reply_markup=keyboard_preview,
            parse_mode="Markdown"
        )

# --- Действия модерации ---
@dp.callback_query(lambda c: c.data.startswith("sendmod_") or c.data.startswith("cancel_"))
async def handle_preview_actions(cq: types.CallbackQuery):
    user_id = int(cq.data.split("_")[1])
    if cq.data.startswith("sendmod_"):
        ad = pending_ads.get(user_id)
        if ad:
            # Отправляем на модерацию админу
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
            await cq.message.edit_reply_markup()
            await cq.answer("Объявление отправлено на модерацию!")
            del ads_data[user_id]
        else:
            await cq.answer("Объявление не найдено.")
    elif cq.data.startswith("cancel_"):
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление отменено.")

# --- Запуск бота ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
