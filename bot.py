import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

API_TOKEN = os.getenv("API_TOKEN", "8219073859:AAH2qL0-w9mQTxGOFNqv-svRALHFQ8MDorw")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command(commands=["start"]))
async def start(msg: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Подать объявление", callback_data="new_ad")],
        [InlineKeyboardButton("Правила", callback_data="rules")],
        [InlineKeyboardButton("Связаться с админом", url="https://t.me/saltrew")]
    ])
    await msg.answer("Здравствуйте, я официальный бот канала AutoHub62!")
    await msg.answer("Выберите действие:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "rules")
async def rules(cq: types.CallbackQuery):
    await cq.message.answer(
        "Правила подачи объявления:\n"
        "1. Все поля обязательны\n"
        "2. Фото — до 10 шт.\n"
        "3. Указывайте реальные цены\n"
        "4. Контакт обязателен"
    )

@dp.callback_query(lambda c: c.data == "new_ad")
async def new_ad(cq: types.CallbackQuery):
    await cq.message.answer("Функция подачи объявлений пока отключена (демо).")

async def handle(request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(update)
    return web.Response(text="ok")

app = web.Application()
app.router.add_post("/bot", handle)  # endpoint для Bothost

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    web.run_app(app, port=port)
