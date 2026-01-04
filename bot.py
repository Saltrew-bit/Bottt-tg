import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.filters import CommandStart

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8219073859:AAH2qL0-w9mQTxGOFNqv-svRALHFQ8MDorw"
ADMIN_ID = 1688416529
CHANNEL_ID = "@AutoHub62Channel"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

ads_data = {}
pending_ads = {}

# /start с кнопками
@dp.message(CommandStart())
async def start(msg: types.Message):
    if msg.chat.type == "private":
        try:
            await msg.delete()
        except Exception:
            pass

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Подать объявление", callback_data="new_ad")],
        [InlineKeyboardButton(text="📜 Правила", callback_data="rules")],
        [InlineKeyboardButton(text="👨‍💼 Связь с админом", url="https://t.me/saltrew")]
    ])
    await msg.answer(
        "👋 Здравствуйте!\n"
        "Я официальный бот канала **AutoHub62**.\n"
        "Помогаю удобно размещать объявления о продаже автомобилей.\n\n"
        "Выберите действие ниже ⬇️",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# Правила
@dp.callback_query(lambda c: c.data == "rules")
async def rules(cq: types.CallbackQuery):
    await cq.message.answer(
        "📜 *Правила размещения объявлений:*\n"
        "1. Авто в Рязани или области\n"
        "2. Реальная цена\n"
        "3. Контакт обязателен\n"
        "4. Описание от владельца приветствуется\n"
        "5. Фото до 10 шт.",
        parse_mode="Markdown"
    )

# Начало подачи объявления
@dp.callback_query(lambda c: c.data == "new_ad")
async def new_ad(cq: types.CallbackQuery):
    user_id = cq.from_user.id
    ads_data[user_id] = {"step": 1, "data": {}}
    await cq.message.answer("Введите марку и модель автомобиля:")

# Обработка шагов подачи объявления
@dp.message()
async def process_ad(msg: types.Message):
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
            await msg.answer("Год должен быть числом. Попробуйте снова:")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("Введите цену (₽, только цифры):")
    elif step == 3:
        if not msg.text.isdigit():
            await msg.answer("Цена должна быть числом. Попробуйте снова:")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("Введите пробег (км, только цифры):")
    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("Пробег должен быть числом. Попробуйте снова:")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer("Введите описание автомобиля (коротко, от владельца):")
    elif step == 5:
        ad["description"] = msg.text
        ads_data[user_id]["step"] = 6
        await msg.answer("Отправьте фото автомобиля (до 10 шт). Когда закончите, напишите 'стоп'.")
    elif step == 6:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"Фото принято ({len(ad['photos'])}/10). Можно прислать ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 7
                await msg.answer("Фото завершены. Введите контакт (телефон или Telegram):")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 7
            await msg.answer("Фото завершены. Введите контакт (телефон или Telegram):")
        else:
            await msg.answer("Отправьте фото или напишите 'стоп'.")
    elif step == 7:
        ad["contact"] = msg.text
        pending_ads[user_id] = ad
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

        if media:
            await bot.send_media_group(chat_id=ADMIN_ID, media=media)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Опубликовать в канал", callback_data=f"publish_{user_id}")],
            [InlineKeyboardButton(text="❌ Удалить объявление", callback_data=f"delete_{user_id}")]
        ])
        await bot.send_message(chat_id=ADMIN_ID, text=text, reply_markup=keyboard)
        await msg.answer("Объявление принято и отправлено на модерацию.")
        del ads_data[user_id]

# Действия администратора
@dp.callback_query(lambda c: c.data.startswith("publish_") or c.data.startswith("delete_"))
async def admin_actions(cq: types.CallbackQuery):
    if cq.from_user.id != ADMIN_ID:
        await cq.answer("Только админ может управлять объявлениями.")
        return
    data = cq.data
    uid = int(data.split("_")[1])
    ad = pending_ads.get(uid)
    if data.startswith("publish_") and ad:
        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
        text = (
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📝 {ad['description']}\n"
            f"📞 {ad['contact']}"
        )
        if media:
            await bot.send_media_group(chat_id=CHANNEL_ID, media=media)
        await bot.send_message(chat_id=CHANNEL_ID, text=text)
        del pending_ads[uid]
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление опубликовано!")
    elif data.startswith("delete_"):
        pending_ads.pop(uid, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление удалено.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
