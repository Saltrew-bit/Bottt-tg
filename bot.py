import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

BOT_TOKEN = "8219073859:AAH2qL0-w9mQTxGOFNqv-svRALHFQ8MDorw"
ADMIN_ID = 1688416529  # твой Telegram ID для модерации

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

ads_data = {}
pending_ads = {}

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

@dp.callback_query(lambda c: c.data == "rules")
async def rules(callback: types.CallbackQuery):
    await callback.message.answer(
        "📜 *Правила размещения объявлений:*\n\n"
        "• Авто в Рязани или области\n"
        "• Реальная цена\n"
        "• Контакт обязателен\n"
        "• Описание обязательно\n"
        "• До 10 фото\n\n"
        "Соблюдайте правила для быстрой публикации.",
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(callback: types.CallbackQuery):
    ads_data[callback.from_user.id] = {"step": 1, "data": {}}
    await callback.message.answer(
        "🚗 *Шаг 1:* Введите марку и модель автомобиля\n"
        "_Пример: Toyota Camry_",
        parse_mode="Markdown"
    )

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
            "📅 *Шаг 2:* Введите год выпуска\n"
            "_Пример: 2015_",
            parse_mode="Markdown"
        )
    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("❌ Введите год числом, например 2015")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer(
            "💰 *Шаг 3:* Введите цену (₽)\n"
            "_Пример: 750000_",
            parse_mode="Markdown"
        )
    elif step == 3:
        if not msg.text.isdigit():
            await msg.answer("❌ Введите цену числом, например 750000")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer(
            "📏 *Шаг 4:* Введите пробег (км)\n"
            "_Пример: 85000_",
            parse_mode="Markdown"
        )
    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("❌ Введите пробег числом, например 85000")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer(
            "✏️ *Шаг 5:* Добавьте описание автомобиля\n"
            "_Пример: Отличное состояние, один владелец, все ТО по регламенту_",
            parse_mode="Markdown"
        )
    elif step == 5:
        ad["description"] = msg.text
        ads_data[user_id]["step"] = 6
        await msg.answer(
            "📸 *Шаг 6:* Отправьте фото автомобиля (до 10 шт).\n"
            "Когда закончите — напишите 'стоп'.",
            parse_mode="Markdown"
        )
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

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
