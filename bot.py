import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "ТВОЙ_ТОКЕН_ОСТАВЬ_КАК_ЕСТЬ"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_steps = {}
user_data = {}

@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚗 Подать объявление", callback_data="add_ad")],
            [InlineKeyboardButton(text="📜 Правила", callback_data="rules")],
            [InlineKeyboardButton(text="👨‍💼 Связь с админом", url="https://t.me/saltrew")]
        ]
    )

    await message.answer(
        "👋 Здравствуйте!\n\n"
        "Я официальный бот канала AutoHub62.\n"
        "Помогу вам разместить объявление о продаже автомобиля.\n\n"
        "Выберите действие ⬇️",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "rules")
async def rules(callback: types.CallbackQuery):
    await callback.message.answer(
        "📜 Правила:\n"
        "• Реальные цены\n"
        "• Авто в Рязани или области\n"
        "• Контакт обязателен"
    )

@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(callback: types.CallbackQuery):
    user_steps[callback.from_user.id] = 1
    user_data[callback.from_user.id] = {}
    await callback.message.answer("Введите марку и модель автомобиля:")

@dp.message()
async def ad_steps(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_steps:
        return

    step = user_steps[user_id]

    if step == 1:
        user_data[user_id]["model"] = message.text
        user_steps[user_id] = 2
        await message.answer("Введите год выпуска:")

    elif step == 2:
        user_data[user_id]["year"] = message.text
        user_steps[user_id] = 3
        await message.answer("Введите цену:")

    elif step == 3:
        user_data[user_id]["price"] = message.text
        user_steps[user_id] = 4
        await message.answer("Введите контакт для связи:")

    elif step == 4:
        user_data[user_id]["contact"] = message.text

        data = user_data[user_id]
        await message.answer(
            "✅ Объявление принято!\n\n"
            f"🚗 {data['model']}\n"
            f"📅 {data['year']}\n"
            f"💰 {data['price']}\n"
            f"📞 {data['contact']}\n\n"
            "После модерации оно появится в канале AutoHub62."
        )

        del user_steps[user_id]
        del user_data[user_id]

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
