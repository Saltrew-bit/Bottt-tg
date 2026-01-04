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

# --- /start ---
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
        "👋 *Здравствуйте!*\n\n"
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
        "1️⃣ Авто в Рязани или области\n"
        "2️⃣ Реальная цена\n"
        "3️⃣ Контакт обязателен\n"
        "4️⃣ Фото до 10 шт.\n"
        "5️⃣ Описание от владельца обязательно\n\n"
        "Следуйте этим правилам, чтобы объявление прошло модерацию.",
        parse_mode="Markdown"
    )

# --- Подача объявления ---
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(callback: types.CallbackQuery):
    ads_data[callback.from_user.id] = {"step": 1, "data": {}}
    await callback.message.answer("🚗 Введите *марку и модель автомобиля*\nПример: Toyota Corolla", parse_mode="Markdown")

# --- Обработка шагов ---
@dp.message()
async def process_message(msg: types.Message):
    user_id = msg.from_user.id
    if user_id not in ads_data:
        return
    step = ads_data[user_id]["step"]
    ad = ads_data[user_id]["data"]

    if step == 1:
        ad["model"] = msg.text
        ads_data[user_id]["step"] = 2
        await msg.answer("📅 Введите *год выпуска* (только цифры)\nПример: 2015", parse_mode="Markdown")
    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("❌ Ошибка! Введите год цифрами. Пример: 2015")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("💰 Введите *цену* (только цифры, без ₽)\nПример: 450.000", parse_mode="Markdown")
    elif step == 3:
        text = msg.text.replace(".", "")
        if not text.isdigit():
            await msg.answer("❌ Ошибка! Введите цену цифрами. Пример: 450.000")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("📏 Введите *пробег* (только цифры, км)\nПример: 120.000", parse_mode="Markdown")
    elif step == 4:
        text = msg.text.replace(".", "")
        if not text.isdigit():
            await msg.answer("❌ Ошибка! Введите пробег цифрами. Пример: 120.000")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer("📝 Напишите *описание автомобиля*\nПример: Отличное состояние, 2 владельца, бензин 1.6", parse_mode="Markdown")
    elif step == 5:
        ad["description"] = msg.text
        ads_data[user_id]["step"] = 6
        await msg.answer("📸 Отправьте фото автомобиля (до 10 шт.). Когда закончите, напишите 'стоп'.")
    elif step == 6:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"✅ Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 7
                await msg.answer("Фото завершены. Теперь введите *контакт* (телефон или @ник):", parse_mode="Markdown")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 7
            await msg.answer("Фото завершены. Теперь введите *контакт* (телефон или @ник):", parse_mode="Markdown")
        else:
            await msg.answer("❗ Отправьте фото или напишите 'стоп'.")
    elif step == 7:
        ad["contact"] = msg.text
        pending_ads[user_id] = ad

        text = (
            f"🚗 *{ad['model']}*\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📝 {ad['description']}\n"
            f"📞 {ad['contact']}\n\n"
            f"От {msg.from_user.full_name}"
        )

        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
        if media:
            await bot.send_media_group(ADMIN_ID, media)

        await bot.send_message(
            ADMIN_ID,
            text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton("✅ Опубликовать", callback_data=f"publish_{user_id}")],
                    [InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{user_id}")]
                ]
            ),
            parse_mode="Markdown"
        )

        await msg.answer("🎉 Ваше объявление приятно и отправлено на модерацию!")
        del ads_data[user_id]

# --- Админ ---
@dp.callback_query(lambda c: c.data.startswith("publish_") or c.data.startswith("delete_"))
async def handle_admin(cq: types.CallbackQuery):
    if cq.from_user.id != ADMIN_ID:
        await cq.answer("❌ Только админ может управлять объявлениями.")
        return
    user_id = int(cq.data.split("_")[1])
    if cq.data.startswith("publish_"):
        ad = pending_ads.get(user_id)
        if ad:
            text = (
                f"🚗 *{ad['model']}*\n"
                f"📅 {ad['year']}\n"
                f"💰 {ad['price']} ₽\n"
                f"📏 {ad['mileage']} км\n"
                f"📝 {ad['description']}\n"
                f"📞 {ad['contact']}"
            )
            media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
            if media:
                await bot.send_media_group(CHANNEL_ID, media)
            await bot.send_message(CHANNEL_ID, text, parse_mode="Markdown")
            del pending_ads[user_id]
            await cq.message.edit_reply_markup()
            await cq.answer("✅ Объявление опубликовано!")
        else:
            await cq.answer("❌ Объявление не найдено.")
    elif cq.data.startswith("delete_"):
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("❌ Объявление удалено.")

# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
