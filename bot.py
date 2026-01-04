import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.filters import Command

API_TOKEN = os.getenv("API_TOKEN")  # либо вставь прямо токен
ADMIN_ID = 1688416529  # твой Telegram ID
CHANNEL_ID = "@AutoHub62Channel"  # канал для публикации

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

ads_data = {}
pending_ads = {}

@dp.message(Command(commands=["start"]))
async def start(msg: types.Message):
    if msg.chat.type == "private":
        try:
            await msg.delete()
        except Exception:
            pass

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🚗 Подать объявление", callback_data="new_ad")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules")],
        [InlineKeyboardButton("👨‍💼 Связь с админом", url="https://t.me/saltrew")]
    ])
    await msg.answer(
        "👋 Здравствуйте!\n\n"
        "Я официальный бот канала **AutoHub62**.\n"
        "Помогаю удобно размещать объявления о продаже автомобилей.\n\n"
        "Выберите действие ниже ⬇️",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data in ["rules", "new_ad"])
async def handle_buttons(cq: types.CallbackQuery):
    if cq.data == "rules":
        await cq.message.answer(
            "📜 *Правила подачи объявления:*\n"
            "1. Все поля обязательны\n"
            "2. Фото — до 10 шт.\n"
            "3. Указывайте реальные цены\n"
            "4. Контакт обязателен",
            parse_mode="Markdown"
        )
    elif cq.data == "new_ad":
        ads_data[cq.from_user.id] = {"step": 1, "data": {}}
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
        await msg.answer("Отправьте фото автомобиля (до 10 шт.). Когда закончите, напишите 'стоп'.")
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
        ads_data[user_id]["step"] = 8

        text = (
            f"Новое объявление от {msg.from_user.full_name}:\n\n"
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📝 {ad['description']}\n"
            f"📞 {ad['contact']}"
        )

        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
        pending_ads[user_id] = ad

        if media:
            await bot.send_media_group(ADMIN_ID, media)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("✅ Опубликовать в канал", callback_data=f"publish_{user_id}")],
            [InlineKeyboardButton("❌ Удалить объявление", callback_data=f"delete_{user_id}")]
        ])
        await bot.send_message(ADMIN_ID, text, reply_markup=keyboard)
        await msg.answer("Ваше объявление успешно создано и отправлено на модерацию!")
        del ads_data[user_id]

@dp.callback_query(lambda c: c.data.startswith("publish_") or c.data.startswith("delete_"))
async def handle_admin_actions(cq: types.CallbackQuery):
    if cq.from_user.id != ADMIN_ID:
        await cq.answer("Только админ может управлять объявлениями.")
        return

    data = cq.data
    user_id = int(data.split("_")[1])
    if data.startswith("publish_"):
        ad = pending_ads.get(user_id)
        if ad:
            text = (
                f"🚗 {ad['model']}\n"
                f"📅 {ad['year']}\n"
                f"💰 {ad['price']} ₽\n"
                f"📏 {ad['mileage']} км\n"
                f"📝 {ad['description']}\n"
                f"📞 {ad['contact']}"
            )
            media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
            if media:
                await bot.send_media_group(CHANNEL_ID, media)
            await bot.send_message(CHANNEL_ID, text)
            del pending_ads[user_id]
            await cq.message.edit_reply_markup()
            await cq.answer("Объявление опубликовано!")
        else:
            await cq.answer("Объявление не найдено.")
    elif data.startswith("delete_"):
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление удалено.")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
