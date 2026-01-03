import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram import executor

API_TOKEN = "8219073859:AAH2qL0-w9mQTxGOFNqv-svRALHFQ8MDorw"
ADMIN_ID = 1688416529
CHANNEL_ID = "@AutoHub62"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

ads_data = {}
pending_ads = {}

@dp.message(Command("start"))
async def start_handler(msg: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Подать объявление", callback_data="new_ad")],
        [InlineKeyboardButton("Правила", callback_data="rules")],
        [InlineKeyboardButton("Связаться с админом", url="https://t.me/saltrew")]
    ])
    await msg.answer("Здравствуйте, я официальный бот канала AutoHub62!")
    await msg.answer("Выберите действие:", reply_markup=keyboard)

@dp.callback_query(Text("rules"))
async def rules_handler(cq: types.CallbackQuery):
    await cq.message.answer(
        "Правила подачи объявления:\n"
        "1. Все поля обязательны\n"
        "2. Фото — до 10 шт.\n"
        "3. Указывайте реальные цены\n"
        "4. Контакт обязателен"
    )

@dp.callback_query(Text("new_ad"))
async def new_ad_handler(cq: types.CallbackQuery):
    ads_data[cq.from_user.id] = {"step": 1, "data": {}}
    await cq.message.answer("Введите марку и модель автомобиля:")

@dp.message()
async def ads_message_handler(msg: types.Message):
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
        await msg.answer("Отправьте фото автомобиля (до 10). Когда закончите, напишите 'стоп'.")
    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 6
                await msg.answer("Фото завершены. Введите контакт:")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer("Фото завершены. Введите контакт:")
        else:
            await msg.answer("Отправьте фото или напишите 'стоп'.")
    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        pending_ads[user_id] = ad
        text = (
            f"Новое объявление от {msg.from_user.full_name}:\n\n"
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📞 {ad['contact']}"
        )
        media = [InputMediaPhoto(pid) for pid in ad.get("photos", [])]
        if media:
            await bot.send_media_group(ADMIN_ID, media)
        await bot.send_message(ADMIN_ID, text)
        await msg.answer("Ваше объявление отправлено на модерацию. Спасибо!")
        del ads_data[user_id]

@dp.callback_query(Text(startswith="publish_"))
async def publish_handler(cq: types.CallbackQuery):
    if cq.from_user.id != ADMIN_ID:
        await cq.answer("Только админ может управлять объявлениями.")
        return
    user_id = int(cq.data.split("_")[1])
    ad = pending_ads.get(user_id)
    if ad:
        text = (
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📞 {ad['contact']}"
        )
        media = [InputMediaPhoto(pid) for pid in ad.get("photos", [])]
        if media:
            await bot.send_media_group(CHANNEL_ID, media)
        await bot.send_message(CHANNEL_ID, text)
        del pending_ads[user_id]
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление опубликовано!")

@dp.callback_query(Text(startswith="delete_"))
async def delete_handler(cq: types.CallbackQuery):
    if cq.from_user.id != ADMIN_ID:
        await cq.answer("Только админ может управлять объявлениями.")
        return
    user_id = int(cq.data.split("_")[1])
    pending_ads.pop(user_id, None)
    await cq.message.edit_reply_markup()
    await cq.answer("Объявление удалено!")

if __name__ == "__main__":
    print("Бот AutoHub62 запущен...")
    executor.start_polling(dp, skip_updates=True)
