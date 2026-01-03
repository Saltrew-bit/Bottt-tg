from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = "8219073859:AAH2qL0-w9mQTxGOFNqv-svRALHFQ8MDorw"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer("Здравствуйте, я официальный бот канала AutoHub62!")

if __name__ == "__main__":
    print("Бот AutoHub62 запущен...")
    executor.start_polling(dp, skip_updates=True)
