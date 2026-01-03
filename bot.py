import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = "8219073859:AAH2qL0-w9mQTxGOFNqv-svRALHFQ8MDorw"
ADMIN_ID = 1688416529
CHANNEL_ID = "@AutoHub62"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot=bot)

@dp.message(Command(commands=["start"]))
async def start_handler(msg: types.Message):
    await msg.answer(
        "Здравствуйте, я официальный бот канала AutoHub62!\n"
        f"Все объявления публикуются в канале {CHANNEL_ID}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Перейти в канал", url=f"https://t.me/{CHANNEL_ID[1:]}")],
        [InlineKeyboardButton("Связаться с админом", url="https://t.me/saltrew")]
    ])
    await msg.answer("Выберите действие:", reply_markup=keyboard)

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
