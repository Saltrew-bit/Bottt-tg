import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8219073859:AAH2qL0-w9mQTxGOFNqv-svRALHFQ8MDorw"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def show_start_button(message: types.Message):
    if message.text in ["/start", "start", "Старт", "начать"]:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("🚗 Подать объявление", callback_data="add_ad")],
            [InlineKeyboardButton("📜 Правила", callback_data="rules")],
            [InlineKeyboardButton("👨‍💼 Связь с админом", url="https://t.me/saltrew")]
        ])
        await message.answer(
            "👋 Здравствуйте!\nЯ официальный бот канала **AutoHub62**.\nВыберите действие ниже ⬇️",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
