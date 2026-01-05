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

# ---------- START ----------
@dp.message(CommandStart())
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Подать объявление", callback_data="add_ad")],
        [InlineKeyboardButton(text="📜 Правила", callback_data="rules")]
    ])
    await message.answer("Добро пожаловать в AutoHub62", reply_markup=keyboard)

# ---------- RULES ----------
@dp.callback_query(lambda c: c.data == "rules")
async def rules(c: types.CallbackQuery):
    await c.message.answer("Правила простые: честное описание, реальные цены.")
    await c.answer()

# ---------- ADD AD ----------
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(c: types.CallbackQuery):
    ads_data[c.from_user.id] = {"step": 1, "data": {}}
    await c.message.answer("Введите марку и модель:")
    await c.answer()

# ---------- MAIN MESSAGE HANDLER ----------
@dp.message()
async def process_message(msg: types.Message):
    user_id = msg.from_user.id

    # ----- EDIT MODE -----
    if user_id in ads_data:
        step = ads_data[user_id]["step"]
        ad = ads_data[user_id]["data"]

        if isinstance(step, str) and step.startswith("edit_"):
            field = step.replace("edit_", "")
            ad[field] = msg.text
            pending_ads[user_id] = ad
            await send_user_preview(user_id)
            del ads_data[user_id]
            return

    if user_id not in ads_data:
        return

    step = ads_data[user_id]["step"]
    ad = ads_data[user_id]["data"]

    if step == 1:
        ad["model"] = msg.text
        ads_data[user_id]["step"] = 2
        await msg.answer("Год выпуска:")

    elif step == 2:
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("Цена:")

    elif step == 3:
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("Пробег:")

    elif step == 4:
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer("Отправьте фото, затем напишите 'стоп'")

    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer("Контакт:")

    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer("Краткое описание:")

    elif step == 7:
        ad["description"] = msg.text
        pending_ads[user_id] = ad
        await send_user_preview(user_id)
        del ads_data[user_id]

# ---------- USER PREVIEW ----------
async def send_user_preview(user_id: int):
    ad = pending_ads[user_id]

    text = (
        f"🚗 {ad['model']}\n"
        f"📅 {ad['year']}\n"
        f"💰 {ad['price']}\n"
        f"📏 {ad['mileage']}\n"
        f"📞 {ad['contact']}\n"
        f"📝 {ad['description']}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="user_edit")],
        [InlineKeyboardButton(text="✅ На модерацию", callback_data="to_moderation")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]
    ])

    if ad.get("photos"):
        await bot.send_media_group(user_id, [InputMediaPhoto(media=p) for p in ad["photos"]])
    await bot.send_message(user_id, text, reply_markup=kb)

# ---------- USER ACTIONS ----------
@dp.callback_query(lambda c: c.data in {"cancel", "user_edit", "to_moderation"})
async def user_actions(c: types.CallbackQuery):
    uid = c.from_user.id

    if c.data == "cancel":
        pending_ads.pop(uid, None)
        await c.message.answer("Отменено. Можете подать объявление заново.", reply_markup=
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚗 Подать объявление", callback_data="add_ad")]
            ])
        )

    elif c.data == "user_edit":
        ads_data[uid] = {"step": "edit_description", "data": pending_ads[uid]}
        await c.message.answer("Введите новое описание:")

    elif c.data == "to_moderation":
        await send_admin_preview(uid)
        await c.message.answer("Отправлено на модерацию")

    await c.answer()

# ---------- ADMIN PREVIEW ----------
async def send_admin_preview(user_id: int):
    ad = pending_ads[user_id]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_edit_{user_id}")],
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"publish_{user_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_id}")]
    ])

    if ad.get("photos"):
        await bot.send_media_group(ADMIN_ID, [InputMediaPhoto(media=p) for p in ad["photos"]])
    await bot.send_message(ADMIN_ID, f"Объявление от {user_id}", reply_markup=kb)

# ---------- ADMIN ACTIONS ----------
@dp.callback_query(lambda c: c.data.startswith(("admin_edit_", "publish_", "reject_")))
async def admin_actions(c: types.CallbackQuery):
    uid = int(c.data.split("_")[1])

    if c.data.startswith("admin_edit"):
        ads_data[ADMIN_ID] = {"step": "edit_description", "data": pending_ads[uid]}
        await c.message.answer("Введите новое описание:")

    elif c.data.startswith("publish"):
        await bot.send_message(CHANNEL_ID, pending_ads[uid]["description"])
        await bot.send_message(uid, "Ваше объявление опубликовано!")
        pending_ads.pop(uid, None)

    elif c.data.startswith("reject"):
        await bot.send_message(uid, "Объявление отклонено")
        pending_ads.pop(uid, None)

    await c.answer()

# ---------- RUN ----------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
