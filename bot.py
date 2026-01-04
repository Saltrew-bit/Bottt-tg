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
        "🚘 *AutoHub62 — продажа автомобилей*\n\n"
        "Здесь вы можете быстро и удобно подать объявление\n"
        "о продаже автомобиля в Рязани и области.\n\n"
        "⏱ Подача занимает 2–3 минуты\n"
        "📸 До 10 фотографий\n"
        "🛡 Все объявления проходят модерацию\n\n"
        "Выберите действие ⬇️",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# --- Правила ---
@dp.callback_query(lambda c: c.data == "rules")
async def rules(callback: types.CallbackQuery):
    await callback.message.answer(
        "📜 *Правила размещения объявлений*\n\n"
        "1️⃣ Автомобиль находится в Рязани или области\n"
        "2️⃣ Указывайте реальную цену без обмана\n"
        "3️⃣ Контакт для связи обязателен\n"
        "4️⃣ Фото должны быть живые, без скриншотов\n"
        "5️⃣ Один автомобиль — одно объявление\n\n"
        "❗ Объявления с фейковыми данными не публикуются",
        parse_mode="Markdown"
    )

# --- Начало подачи объявления ---
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(callback: types.CallbackQuery):
    ads_data[callback.from_user.id] = {"step": 1, "data": {}}
    await callback.message.answer(
        "🚗 *Марка и модель*\n\n"
        "Например:\n"
        "• Lada Vesta\n"
        "• Toyota Camry\n"
        "• BMW 3 Series",
        parse_mode="Markdown"
    )

# --- Обработка сообщений ---
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
        await msg.answer(
            "📅 *Год выпуска автомобиля*\n\n"
            "Пример:\n"
            "2014",
            parse_mode="Markdown"
        )

    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("Введите год **только цифрами**.")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer(
            "💰 *Цена автомобиля*\n\n"
            "Формат:\n"
            "450.000",
            parse_mode="Markdown"
        )

    elif step == 3:
        if not msg.text.replace(".", "").isdigit():
            await msg.answer("Цена должна содержать только цифры.")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer(
            "📏 *Пробег автомобиля (км)*\n\n"
            "Пример:\n"
            "185000",
            parse_mode="Markdown"
        )

    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("Пробег вводится **только цифрами**.")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer(
            "📸 *Фотографии автомобиля*\n\n"
            "• До 10 фото\n"
            "• Общий вид, салон, состояние\n\n"
            "Когда закончите — напишите *стоп*",
            parse_mode="Markdown"
        )

    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            await msg.answer(f"Фото принято ({len(ad['photos'])}/10).")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer(
                "📞 *Контакт для связи*\n\n"
                "Телефон или @username",
                parse_mode="Markdown"
            )

    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer(
            "📝 *Описание от владельца*\n\n"
            "Пример:\n"
            "Хорошее состояние, без ДТП,\n"
            "обслуживался вовремя.",
            parse_mode="Markdown"
        )

    elif step == 7:
        ad["description"] = msg.text
        pending_ads[user_id] = ad

        text = (
            f"🚗 *{ad['model']}*\n"
            f"📅 Год: {ad['year']}\n"
            f"💰 Цена: {ad['price']} ₽\n"
            f"📏 Пробег: {ad['mileage']} км\n"
            f"📞 Контакт: {ad['contact']}\n\n"
            f"📝 {ad['description']}"
        )

        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"publish_{user_id}")],
                [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"delete_{user_id}")]
            ]
        )

        if media:
            await bot.send_media_group(chat_id=ADMIN_ID, media=media)

        await bot.send_message(ADMIN_ID, text, reply_markup=keyboard, parse_mode="Markdown")
        await msg.answer(
            "✅ *Объявление отправлено на модерацию*\n\n"
            "После проверки оно появится в канале.",
            parse_mode="Markdown"
        )
        del ads_data[user_id]

# --- Админ ---
@dp.callback_query(lambda c: c.data.startswith("publish_") or c.data.startswith("delete_"))
async def admin_actions(cq: types.CallbackQuery):
    user_id = int(cq.data.split("_")[1])
    ad = pending_ads.get(user_id)

    if not ad:
        await cq.answer("Объявление не найдено.")
        return

    text = (
        f"🚗 *{ad['model']}*\n"
        f"📅 {ad['year']}\n"
        f"💰 {ad['price']} ₽\n"
        f"📏 {ad['mileage']} км\n"
        f"📞 {ad['contact']}\n\n"
        f"📝 {ad['description']}"
    )

    media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
    if media:
        await bot.send_media_group(CHANNEL_ID, media)
    await bot.send_message(CHANNEL_ID, text, parse_mode="Markdown")

    pending_ads.pop(user_id, None)
    await cq.message.edit_reply_markup()
    await cq.answer("Готово")

# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
