import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

BOT_TOKEN = "8219073859:AAH2qL0-w9mQTxGOFNqv-svRALHFQ8MDorw"
ADMIN_ID = 1688416529
CHANNEL_ID = "@AutoHub62Channel"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

ads_data = {}
pending_ads = {}
editing_ads = {}

# ───── Старт ─────
@dp.message(CommandStart())
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚗 Подать объявление", callback_data="add_ad")],
            [InlineKeyboardButton(text="📜 Правила", callback_data="rules")],
            [InlineKeyboardButton(text="🛠 Администрация", url="https://t.me/saltrew")]
        ]
    )

    await message.answer(
        "👋 *Добро пожаловать в AutoHub62*\n\n"
        "📍 Регион: *Рязань и область*\n"
        "🚘 Продажа автомобилей через модерацию\n\n"
        "Выберите действие ⬇️",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ───── Правила ─────
@dp.callback_query(lambda c: c.data == "rules")
async def rules(cq: types.CallbackQuery):
    await cq.message.answer(
        "📜 *Правила размещения:*\n\n"
        "• Только Рязань и область\n"
        "• Цена в ₽\n"
        "• Реальные данные\n"
        "• До 10 фото\n"
        "• Контакт обязателен",
        parse_mode="Markdown"
    )
    await cq.answer()

# ───── Начало объявления ─────
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(cq: types.CallbackQuery):
    ads_data[cq.from_user.id] = {"step": 1, "data": {}}
    await cq.message.answer("🚗 *Введите марку и модель:*", parse_mode="Markdown")
    await cq.answer()

# ───── ЕДИНСТВЕННЫЙ обработчик сообщений ─────
@dp.message()
async def process_message(msg: types.Message):
    uid = msg.from_user.id
    if uid not in ads_data:
        return

    step = ads_data[uid]["step"]
    ad = ads_data[uid]["data"]

    if step == 1:
        ad["model"] = msg.text
        ads_data[uid]["step"] = 2
        await msg.answer("📅 *Год выпуска:*", parse_mode="Markdown")

    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("❗ Введите год цифрами")
            return
        ad["year"] = msg.text
        ads_data[uid]["step"] = 3
        await msg.answer("💰 *Цена в ₽:*", parse_mode="Markdown")

    elif step == 3:
        ad["price"] = msg.text
        ads_data[uid]["step"] = 4
        await msg.answer("📏 *Пробег (км):*", parse_mode="Markdown")

    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("❗ Пробег только цифрами")
            return
        ad["mileage"] = msg.text
        ads_data[uid]["step"] = 5
        await msg.answer("📷 Отправьте фото (до 10). Напишите *стоп* когда закончите", parse_mode="Markdown")

    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            await msg.answer(f"Фото {len(ad['photos'])}/10 принято")
        elif msg.text.lower() == "стоп":
            ads_data[uid]["step"] = 6
            await msg.answer("📞 *Контакт:*", parse_mode="Markdown")

    elif step == 6:
        ad["contact"] = msg.text
        ads_data[uid]["step"] = 7
        await msg.answer("📝 *Краткое описание:*", parse_mode="Markdown")

    elif step == 7:
        ad["description"] = msg.text
        pending_ads[uid] = ad
        ads_data.pop(uid)
        await send_preview_user(uid)

# ───── Предпросмотр пользователю ─────
async def send_preview_user(uid: int):
    ad = pending_ads[uid]

    text = (
        "📢 *Предпросмотр объявления*\n\n"
        f"🚗 {ad['model']}\n"
        f"📅 {ad['year']}\n"
        f"💰 {ad['price']} ₽\n"
        f"📏 {ad['mileage']} км\n"
        f"📞 {ad['contact']}\n"
        f"📝 {ad['description']}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ На модерацию", callback_data=f"to_moderation_{uid}"),
                InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_menu_{uid}")
            ],
            [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{uid}")]
        ]
    )

    if ad.get("photos"):
        await bot.send_media_group(
            uid, [InputMediaPhoto(media=p) for p in ad["photos"]]
        )
    await bot.send_message(uid, text, parse_mode="Markdown", reply_markup=keyboard)

# ───── Меню редактирования ─────
@dp.callback_query(lambda c: c.data.startswith("edit_menu_"))
async def edit_menu(cq: types.CallbackQuery):
    uid = int(cq.data.split("_")[-1])
    ads_data[uid] = {"step": 1, "data": pending_ads[uid]}
    await cq.message.answer("✏️ Начинаем редактирование.\nВведите марку и модель:")
    await cq.answer()

# ───── Модерация ─────
@dp.callback_query(lambda c: c.data.startswith("to_moderation_"))
async def to_moderation(cq: types.CallbackQuery):
    uid = int(cq.data.split("_")[-1])
    ad = pending_ads[uid]

    text = (
        "🛂 *На модерацию*\n\n"
        f"🚗 {ad['model']}\n"
        f"📅 {ad['year']}\n"
        f"💰 {ad['price']} ₽\n"
        f"📏 {ad['mileage']} км\n"
        f"📞 {ad['contact']}\n"
        f"📝 {ad['description']}"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"publish_{uid}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"delete_{uid}")
            ]
        ]
    )

    if ad.get("photos"):
        await bot.send_media_group(
            ADMIN_ID, [InputMediaPhoto(media=p) for p in ad["photos"]]
        )
    await bot.send_message(ADMIN_ID, text, parse_mode="Markdown", reply_markup=kb)
    await cq.answer("Отправлено на модерацию")

# ───── Публикация ─────
@dp.callback_query(lambda c: c.data.startswith("publish_"))
async def publish(cq: types.CallbackQuery):
    uid = int(cq.data.split("_")[-1])
    ad = pending_ads.pop(uid)

    if ad.get("photos"):
        await bot.send_media_group(
            CHANNEL_ID, [InputMediaPhoto(media=p) for p in ad["photos"]]
        )

    await bot.send_message(
        CHANNEL_ID,
        f"🚗 {ad['model']}\n📅 {ad['year']}\n💰 {ad['price']} ₽\n📏 {ad['mileage']} км\n📞 {ad['contact']}\n📝 {ad['description']}"
    )

    await bot.send_message(uid, "✅ Объявление опубликовано")
    await cq.answer()

# ───── Запуск ─────
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
