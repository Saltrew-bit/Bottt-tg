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

# ---------- Клавиатуры ----------

def start_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚗 Подать объявление", callback_data="add_ad")],
            [InlineKeyboardButton(text="📜 Правила", callback_data="rules")],
            [InlineKeyboardButton(text="👨‍💼 Связь с админом", url="https://t.me/saltrew")]
        ]
    )

def preview_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить на модерацию", callback_data="send_preview")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_preview")]
        ]
    )

# ---------- Старт ----------

@dp.message(CommandStart())
async def start(message: types.Message):
    if message.chat.type == "private":
        try:
            await message.delete()
        except Exception:
            pass

    await message.answer(
        "👋 Здравствуйте!\n\n"
        "Я бот канала *AutoHub62*.\n"
        "Помогаю удобно размещать объявления о продаже авто.\n\n"
        "Выберите действие ⬇️",
        reply_markup=start_keyboard(),
        parse_mode="Markdown"
    )

# ---------- Правила ----------

@dp.callback_query(lambda c: c.data == "rules")
async def rules(callback: types.CallbackQuery):
    await callback.message.answer(
        "📜 *Правила размещения:*\n\n"
        "• Реальная цена\n"
        "• Авто в Рязани или области\n"
        "• Контакт обязателен",
        parse_mode="Markdown"
    )

# ---------- Начало подачи ----------

@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(callback: types.CallbackQuery):
    ads_data[callback.from_user.id] = {"step": 1, "data": {}}
    await callback.message.answer("🚗 Введите марку и модель автомобиля:")

# ---------- Шаги ----------

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
        await msg.answer("Введите год выпуска:")

    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("Введите год цифрами.")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("Введите цену (например 450.000):")

    elif step == 3:
        if not msg.text.replace(".", "").isdigit():
            await msg.answer("Цена должна быть цифрами.")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("Введите пробег (км):")

    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("Пробег только цифрами.")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer("Отправьте фото (до 10). Напишите *стоп* когда закончите.")

    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            await msg.answer(f"Фото принято ({len(ad['photos'])}/10)")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer("Введите контакт:")
        else:
            await msg.answer("Отправьте фото или напишите *стоп*.")

    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer("Введите описание:")

    # ---------- ПРЕДПРОСМОТР ----------
    elif step == 7:
        ad["description"] = msg.text
        ads_data[user_id]["step"] = 8

        preview_text = (
            "📝 *Предпросмотр объявления*\n\n"
            f"🚗 *{ad['model']}*\n"
            f"📅 Год: {ad['year']}\n"
            f"💰 Цена: {ad['price']} ₽\n"
            f"📏 Пробег: {ad['mileage']} км\n"
            f"📞 Контакт: {ad['contact']}\n\n"
            f"📝 {ad['description']}"
        )

        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]

        if media:
            await msg.answer_media_group(media)

        await msg.answer(preview_text, reply_markup=preview_keyboard(), parse_mode="Markdown")

# ---------- Кнопки предпросмотра ----------

@dp.callback_query(lambda c: c.data in ["send_preview", "cancel_preview"])
async def handle_preview(cq: types.CallbackQuery):
    user_id = cq.from_user.id

    if user_id not in ads_data:
        await cq.answer("Сессия истекла")
        return

    if cq.data == "cancel_preview":
        ads_data.pop(user_id, None)
        await cq.message.answer("❌ Объявление отменено")
        await cq.answer()
        return

    ad = ads_data[user_id]["data"]
    pending_ads[user_id] = ad

    text = (
        f"Новое объявление:\n\n"
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
            [InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"publish_{user_id}")],
            [InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_{user_id}")]
        ]
    )

    if media:
        await bot.send_media_group(chat_id=ADMIN_ID, media=media)

    await bot.send_message(chat_id=ADMIN_ID, text=text, reply_markup=keyboard)

    ads_data.pop(user_id, None)
    await cq.message.answer("✅ Отправлено на модерацию")
    await cq.answer()

# ---------- Админ ----------

@dp.callback_query(lambda c: c.data.startswith(("publish_", "delete_")))
async def admin_actions(cq: types.CallbackQuery):
    user_id = int(cq.data.split("_")[1])

    if cq.from_user.id != ADMIN_ID:
        await cq.answer("Нет доступа")
        return

    if cq.data.startswith("publish_"):
        ad = pending_ads.pop(user_id, None)
        if not ad:
            await cq.answer("Объявление не найдено")
            return

        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
        if media:
            await bot.send_media_group(chat_id=CHANNEL_ID, media=media)

        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=(
                f"🚗 {ad['model']}\n"
                f"📅 {ad['year']}\n"
                f"💰 {ad['price']} ₽\n"
                f"📏 {ad['mileage']} км\n"
                f"📞 {ad['contact']}\n"
                f"📝 {ad['description']}"
            )
        )

        await cq.message.edit_reply_markup()
        await cq.answer("Опубликовано")

    else:
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Удалено")

# ---------- Запуск ----------

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
