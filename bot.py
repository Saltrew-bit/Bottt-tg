import asyncio
import re
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

# ───── START ─────
@dp.message(CommandStart())
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚗 Подать объявление", callback_data="add_ad")],
            [InlineKeyboardButton(text="📜 Правила", callback_data="rules")],
            [InlineKeyboardButton(text="🛠 Администрация", url="https://t.me/saltrew")]
        ]
    )
    await message.answer(
        "👋 Добро пожаловать в *AutoHub62Bot*\n\n"
        "🚘 Продажа автомобилей в Рязани и области\n\n"
        "Выберите действие ⬇️",
        parse_mode="Markdown",
        reply_markup=kb
    )

# ───── RULES ─────
@dp.callback_query(lambda c: c.data == "rules")
async def rules(cq: types.CallbackQuery):
    await cq.message.answer(
        "📜 *Правила размещения объявлений:*\n\n"
        "1. Авто должно быть в Рязани или области\n"
        "2. Цена реальная, в формате например: 450.000 ₽\n"
        "3. Контакт обязателен, например: номер телефона или @username\n"
        "4. Фото автомобиля до 10 шт.\n"
        "5. Краткое описание приветствуется",
        parse_mode="Markdown"
    )
    await cq.answer()

# ───── ADD AD ─────
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(cq: types.CallbackQuery):
    ads_data[cq.from_user.id] = {"step": 1, "data": {}}
    await cq.message.answer(
        "🚗 Введите марку и модель автомобиля\n"
        "Например: *Lada Vesta*",
        parse_mode="Markdown"
    )
    await cq.answer()

# ───── ONE MESSAGE HANDLER ─────
@dp.message()
async def message_handler(msg: types.Message):
    uid = msg.from_user.id
    if uid not in ads_data:
        return

    step = ads_data[uid]["step"]
    ad = ads_data[uid]["data"]

    if step == 1:
        ad["model"] = msg.text
        ads_data[uid]["step"] = 2
        await msg.answer("📅 Введите год выпуска\nНапример: 2018")

    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("❌ Год — только цифры")
            return
        ad["year"] = msg.text
        ads_data[uid]["step"] = 3
        await msg.answer("💰 Введите цену в ₽\nНапример: 450.000")

    elif step == 3:
        price = re.sub(r"[^\d]", "", msg.text)
        if not price:
            await msg.answer("❌ Цена некорректна")
            return
        ad["price"] = price
        ads_data[uid]["step"] = 4
        await msg.answer("📏 Введите пробег (км)\nНапример: 120000")

    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("❌ Пробег — только цифры")
            return
        ad["mileage"] = msg.text
        ads_data[uid]["step"] = 5
        await msg.answer(
            "📷 Отправьте фото автомобиля (до 10)\n"
            "Когда закончите — напишите *стоп*",
            parse_mode="Markdown"
        )

    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            await msg.answer(f"Фото добавлено ({len(ad['photos'])}/10)")
        elif msg.text.lower() == "стоп":
            ads_data[uid]["step"] = 6
            await msg.answer("📞 Введите контакт (телефон или @username)")

    elif step == 6:
        ad["contact"] = msg.text
        ads_data[uid]["step"] = 7
        await msg.answer("📝 Введите краткое описание")

    elif step == 7:
        ad["description"] = msg.text
        pending_ads[uid] = ad
        ads_data.pop(uid)
        await send_preview(uid)

# ───── PREVIEW ─────
async def send_preview(uid: int):
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

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ На модерацию", callback_data=f"to_mod_{uid}"),
                InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_menu_{uid}")
            ],
            [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{uid}")]
        ]
    )

    if ad.get("photos"):
        await bot.send_media_group(uid, [InputMediaPhoto(media=p) for p in ad["photos"]])
    await bot.send_message(uid, text, parse_mode="Markdown", reply_markup=kb)

# ───── EDIT MENU ─────
@dp.callback_query(lambda c: c.data.startswith("edit_menu_"))
async def edit_menu(cq: types.CallbackQuery):
    uid = int(cq.data.split("_")[-1])
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚗 Марка и модель", callback_data=f"edit_model_{uid}")],
            [InlineKeyboardButton(text="📅 Год", callback_data=f"edit_year_{uid}")],
            [InlineKeyboardButton(text="💰 Цена", callback_data=f"edit_price_{uid}")],
            [InlineKeyboardButton(text="📏 Пробег", callback_data=f"edit_mileage_{uid}")],
            [InlineKeyboardButton(text="📷 Фото", callback_data=f"edit_photos_{uid}")],
            [InlineKeyboardButton(text="📞 Контакт", callback_data=f"edit_contact_{uid}")],
            [InlineKeyboardButton(text="📝 Описание", callback_data=f"edit_desc_{uid}")]
        ]
    )
    await cq.message.answer("✏️ Что вы хотите изменить?", reply_markup=kb)
    await cq.answer()

# ───── MODERATION ─────
@dp.callback_query(lambda c: c.data.startswith("to_mod_"))
async def to_mod(cq: types.CallbackQuery):
    uid = int(cq.data.split("_")[-1])
    ad = pending_ads[uid]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"publish_{uid}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{uid}")
            ]
        ]
    )

    if ad.get("photos"):
        await bot.send_media_group(ADMIN_ID, [InputMediaPhoto(media=p) for p in ad["photos"]])

    await bot.send_message(
        ADMIN_ID,
        f"🛂 Объявление на модерацию\n\n"
        f"{ad['model']} | {ad['year']} | {ad['price']} ₽ | {ad['mileage']} км\n\n"
        f"{ad['description']}",
        reply_markup=kb
    )
    await cq.answer("Отправлено на модерацию")

# ───── ADMIN ACTIONS ─────
@dp.callback_query(lambda c: c.data.startswith(("publish_", "reject_")))
async def admin_actions(cq: types.CallbackQuery):
    uid = int(cq.data.split("_")[-1])
    ad = pending_ads.pop(uid)

    if cq.data.startswith("publish_"):
        if ad.get("photos"):
            await bot.send_media_group(CHANNEL_ID, [InputMediaPhoto(media=p) for p in ad["photos"]])

        await bot.send_message(
            CHANNEL_ID,
            f"{ad['model']} {ad['year']}\n"
            f"{ad['price']} ₽ | {ad['mileage']} км\n"
            f"{ad['contact']}\n\n"
            f"{ad['description']}"
        )
        await bot.send_message(uid, "✅ Ваше объявление опубликовано")

    else:
        await bot.send_message(uid, "❌ Объявление отклонено модератором")

    await cq.answer()

# ───── RUN ─────
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
