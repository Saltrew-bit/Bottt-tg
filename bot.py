import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.filters import Command

# === НАСТРОЙКИ ===
API_TOKEN = "8287039199:AAEesuXU6BHeNgYLXE3A2YZ8RQz9_AzMnNw"  
ADMIN_ID = 1688416529 
CHANNEL_ID = "@Auto62Channel"  

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Временное хранение данных
ads_data = {}
pending_ads = {}

# === СТАРТ И ГЛАВНОЕ МЕНЮ ===
@dp.message(Command("start"))
async def start(msg: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Подать объявление", callback_data="new_ad")],
        [InlineKeyboardButton("Правила", callback_data="rules")],
        [InlineKeyboardButton("Связаться с админом", url="https://t.me/saltrew")]
    ])
    await msg.answer("Добро пожаловать в Авто62! Выберите действие:", reply_markup=keyboard)

# === ОБРАБОТКА КНОПОК ===
@dp.callback_query()
async def handle_buttons(cq: types.CallbackQuery):
    if cq.data == "rules":
        await cq.message.answer(
            "Правила подачи объявления:\n"
            "1. Все поля обязательны\n"
            "2. Фото — до 10 шт.\n"
            "3. Указывайте реальные цены\n"
            "4. Контакт обязателен"
        )
    elif cq.data == "new_ad":
        ads_data[cq.from_user.id] = {"step": 1, "data": {}}
        await cq.message.answer("Введите марку и модель автомобиля:")

# === ПРОЦЕСС ПОДАЧИ ОБЪЯВЛЕНИЯ ===
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
        await msg.answer("Отправьте фото автомобиля (до 10). Когда закончите, напишите 'стоп'.")
    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 6
                await msg.answer("Фото завершены. Введите контакт (Telegram или телефон):")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer("Фото завершены. Введите контакт:")
        else:
            await msg.answer("Отправьте фото или напишите 'стоп'.")
    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7

        # Отправка админу с кнопкой публикации
        text = (
            f"Новое объявление от {msg.from_user.full_name}:\n\n"
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']} ₽\n"
            f"📏 {ad['mileage']} км\n"
            f"📞 {ad['contact']}"
        )
        media = [InputMediaPhoto(pid) for pid in ad.get("photos", [])]

        pending_ads[user_id] = ad

        if media:
            await bot.send_media_group(ADMIN_ID, media)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("✅ Опубликовать в канал", callback_data=f"publish_{user_id}")],
            [InlineKeyboardButton("❌ Удалить объявление", callback_data=f"delete_{user_id}")]
        ])
        await bot.send_message(ADMIN_ID, text, reply_markup=keyboard)

        await msg.answer("Ваше объявление отправлено на модерацию. Спасибо!")
        del ads_data[user_id]

# === ПУБЛИКАЦИЯ И УДАЛЕНИЕ АДМИНОМ ===
@dp.callback_query()
async def handle_admin_actions(cq: types.CallbackQuery):
    data = cq.data
    admin_id = cq.from_user.id
    if admin_id != ADMIN_ID:
        await cq.answer("Только админ может управлять объявлениями.")
        return

    if data.startswith("publish_"):
        user_id = int(data.split("_")[1])
        ad = pending_ads.get(user_id)
        if not ad:
            await cq.answer("Объявление не найдено.")
            return

        # Публикация в канал
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

        # Удаляем кнопку у админа
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление опубликовано!")
        del pending_ads[user_id]

    elif data.startswith("delete_"):
        user_id = int(data.split("_")[1])
        if user_id in pending_ads:
            del pending_ads[user_id]
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление удалено.")

# === ЗАПУСК БОТА ===
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))