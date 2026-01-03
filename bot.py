import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = "8219073859:AAH2qL0-w9mQTxGOFNqv-svRALHFQ8MDorw"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Здравствуйте, я официальный бот канала AutoHub62"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
