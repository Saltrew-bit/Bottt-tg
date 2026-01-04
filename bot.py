import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.filters import CommandStart

API_TOKEN = os.getenv("API_TOKEN")  # или вставь ключ напрямую
ADMIN_ID = 1688416529
CHANNEL_ID = "@AutoHub62Channel"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

ads_data = {}
pending_ads = {}

@dp.message(CommandStart())
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

@dp.callback_query(lambda c: c.data == "rules")
async def rules(callback: types.CallbackQuery):
    await callback.message.answer(
        "📜 *Правила размещения объявлений:*\n\n"
        "1. Авто в Рязани или области\n"
        "2. Реальная цена\n"
        "3. Контакт обязателен\n"
        "4. Описание желательно добавить\n"
        "5. Фото до 10 штук",
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "new_ad")
async def new_ad(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    ads_data[user_id] = {"step": 1, "data": {}}
    await callback.message.answer("🚗 Введите марку и модель автомобиля:")

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
        await msg.answer("Введите год выпуска (только цифры):")
    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("❌ Пожалуйста, укажите год цифрами.")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("Введите цену (₽, только цифры):")
    elif step == 3:
        if not msg.text.isdigit():
            await msg.answer("❌ Пожалуйста, укажите цену цифрами.")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("Введите пробег (км, только цифры):")
    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("❌ Пожалуйста, укажите пробег цифрами.")
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
                await msg.answer("Фото завершены. Введите описание автомобиля:")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer("Фото завершены. Введите описание автомобиля:")
        else:
            await msg.answer("Отправьте фото или напишите 'стоп'.")
    elif step == 6:
        ad["description"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer("Введите контакт для связи (номер или @username):")
    elif step == 7:
        if not msg.text.strip():
            await msg.answer("❌ Пожалуйста, введите контакт для связи.")
            return
        ad["contact"] = msg.text
        text = (
            f"🚗 *Новое объявление от {msg.from_user.full_name}:*\n\n"
            f"**Марка и модель:** {ad['model']}\n"
            f"**Год выпуска:** {ad['year']}\n"
            f"**Цена:** {ad['price']} ₽\n"
            f"**Пробег:** {ad['mileage']} км\n"
            f"**Описание:** {ad['description']}\n"
            f"**Контакт:** {ad['contact']}"
        )
        media = [InputMediaPhoto(pid) for pid in ad.get("photos", [])]
        pending_ads[user_id] = ad
        if media:
            await bot.send_media_group(ADMIN_ID, media)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("✅ Опубликовать", callback_data=f"publish_{user_id}")],
            [InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{user_id}")]
        ])
        await bot.send_message(ADMIN_ID, text, reply_markup=keyboard, parse_mode="Markdown")
        await msg.answer("✅ Ваше объявление принято и отправлено на модерацию!")
        del ads_data[user_id]

@dp.callback_query(lambda c: c.data.startswith("publish_") or c.data.startswith("delete_"))
async def handle_admin(cq: types.CallbackQuery):
    if cq.from_user.id != ADMIN_ID:
        await cq.answer("Только админ может управлять объявлениями.")
        return
    user_id = int(cq.data.split("_")[1])
    if cq.data.startswith("publish_"):
        ad = pending_ads.get(user_id)
        if not ad:
            await cq.answer("Объявление не найдено.")
            return
        text = (
            f"🚗 *{ad['model']}*\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📜 {ad['description']}\n"
            f"📞 {ad['contact']}"
        )
        media = [InputMediaPhoto(pid) for pid in ad.get("photos", [])]
        if media:
            await bot.send_media_group(CHANNEL_ID, media)
        await bot.send_message(CHANNEL_ID, text, parse_mode="Markdown")
        del pending_ads[user_id]
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление опубликовано!")
    elif cq.data.startswith("delete_"):
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление удалено.")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
