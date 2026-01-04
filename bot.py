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

@dp.message(CommandStart())
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🚗 Подать объявление", callback_data="add_ad")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules")],
        [InlineKeyboardButton("👨‍💼 Связь с админом", url="https://t.me/saltrew")]
    ])
    try:
        await message.answer(
            "👋 Здравствуйте!\nЯ официальный бот канала **AutoHub62**.\nВыберите действие ниже ⬇️",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        if message.chat.type == "private":
            await asyncio.sleep(0.5)
            await message.delete()
    except:
        pass

@dp.callback_query(lambda c: c.data in ["rules", "add_ad"])
async def handle_buttons(cq: types.CallbackQuery):
    if cq.data == "rules":
        await cq.message.answer(
            "📌 Правила подачи объявления:\n"
            "1. Все поля обязательны\n"
            "2. Фото — до 10 шт.\n"
            "3. Указывайте реальные цены\n"
            "4. Контакт обязателен"
        )
    elif cq.data == "add_ad":
        user_id = cq.from_user.id
        ads_data[user_id] = {"step": 1, "data": {}}
        await cq.message.answer("Введите марку и модель автомобиля:")

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
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("Введите цену (₽):")
    elif step == 3:
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("Введите пробег (км):")
    elif step == 4:
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer("Введите описание автомобиля:")
    elif step == 5:
        ad["description"] = msg.text
        ads_data[user_id]["step"] = 6
        await msg.answer("Отправьте фото автомобиля (до 10). Когда закончите, напишите 'стоп'.")
    elif step == 6:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 7
                await msg.answer("Фото завершены. Введите контакт:")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 7
            await msg.answer("Фото завершены. Введите контакт:")
        else:
            await msg.answer("Отправьте фото или напишите 'стоп'.")
    elif step == 7:
        ad["contact"] = msg.text
        pending_ads[user_id] = ad
        ads_data.pop(user_id)

        text = (
            f"Новое объявление от {msg.from_user.full_name}:\n\n"
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📝 {ad['description']}\n"
            f"📞 {ad['contact']}"
        )

        media = [InputMediaPhoto(pid) for pid in ad.get("photos", [])]
        if media:
            await bot.send_media_group(ADMIN_ID, media)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("✅ Опубликовать в канал", callback_data=f"publish_{user_id}")],
            [InlineKeyboardButton("❌ Удалить объявление", callback_data=f"delete_{user_id}")]
        ])
        await bot.send_message(ADMIN_ID, text, reply_markup=keyboard)
        await msg.answer("Ваше объявление приятно и отправлено на модерацию.")

@dp.callback_query(lambda c: c.data.startswith(("publish_", "delete_")))
async def handle_admin(cq: types.CallbackQuery):
    user_id = int(cq.data.split("_")[1])
    if cq.from_user.id != ADMIN_ID:
        await cq.answer("Только админ может управлять объявлениями.")
        return

    if cq.data.startswith("publish_"):
        ad = pending_ads.pop(user_id, None)
        if ad:
            text = (
                f"🚗 {ad['model']}\n"
                f"📅 {ad['year']}\n"
                f"💰 {ad['price']} ₽\n"
                f"📏 {ad['mileage']} км\n"
                f"📝 {ad['description']}\n"
                f"📞 {ad['contact']}"
            )
            media = [InputMediaPhoto(pid) for pid in ad.get("photos", [])]
            if media:
                await bot.send_media_group(CHANNEL_ID, media)
            await bot.send_message(CHANNEL_ID, text)
            await cq.message.edit_reply_markup()
            await cq.answer("Объявление опубликовано!")
        else:
            await cq.answer("Объявление не найдено.")
    elif cq.data.startswith("delete_"):
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление удалено.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
