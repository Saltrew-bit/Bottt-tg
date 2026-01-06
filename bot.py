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
editing_mode = {}

FIELDS = [
    ("model", "Введите марку и модель автомобиля:"),
    ("year", "Введите год выпуска (например 2015):"),
    ("price", "Введите цену в ₽ (только цифры):"),
    ("mileage", "Введите пробег в км:"),
    ("photos", "Отправьте фото (до 10). Напишите «стоп» для завершения:"),
    ("contact", "Введите контакт (телефон или @username):"),
    ("description", "Введите краткое описание:")
]

# ---------------- START ----------------
@dp.message(CommandStart())
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Подать объявление", callback_data="add_ad")]
    ])
    await message.answer("Добро пожаловать в AutoHub62", reply_markup=kb)

# ---------------- ADD AD ----------------
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(cb: types.CallbackQuery):
    ads_data[cb.from_user.id] = {"step": 0, "data": {"city": "Рязань"}}
    await cb.message.answer(FIELDS[0][1])

# ---------------- PROCESS ----------------
@dp.message()
async def process(msg: types.Message):
    uid = msg.from_user.id
    if uid not in ads_data:
        return

    state = ads_data[uid]
    step = state["step"]
    key = FIELDS[step][0]

    if key == "photos":
        photos = state["data"].setdefault("photos", [])
        if msg.photo:
            photos.append(msg.photo[-1].file_id)
            if len(photos) >= 10:
                state["step"] += 1
                await msg.answer(FIELDS[state["step"]][1])
        elif msg.text.lower() == "стоп":
            state["step"] += 1
            await msg.answer(FIELDS[state["step"]][1])
        return

    state["data"][key] = msg.text
    state["step"] += 1

    if state["step"] >= len(FIELDS):
        pending_ads[uid] = state["data"]
        del ads_data[uid]
        await send_preview_user(uid)
    else:
        await msg.answer(FIELDS[state["step"]][1])

# ---------------- PREVIEW USER ----------------
async def send_preview_user(uid: int):
    ad = pending_ads[uid]
    text = build_text(ad)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_user_{uid}")],
        [InlineKeyboardButton(text="✅ На модерацию", callback_data=f"to_admin_{uid}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{uid}")]
    ])

    if ad.get("photos"):
        await bot.send_media_group(uid, [InputMediaPhoto(media=p) for p in ad["photos"]])
    await bot.send_message(uid, text, reply_markup=kb)

# ---------------- USER ACTIONS ----------------
@dp.callback_query(lambda c: c.data.startswith(("edit_user_", "cancel_", "to_admin_")))
async def user_actions(cb: types.CallbackQuery):
    uid = int(cb.data.split("_")[-1])

    if cb.data.startswith("edit_user_"):
        editing_mode[uid] = "user"
        ads_data[uid] = {"step": 0, "data": pending_ads[uid]}
        await cb.message.answer("Редактирование начато.")
        await cb.message.answer(FIELDS[0][1])

    elif cb.data.startswith("cancel_"):
        pending_ads.pop(uid, None)
        await cb.message.answer(
            "Объявление отменено",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🚗 Подать объявление", callback_data="add_ad")]]
            )
        )

    elif cb.data.startswith("to_admin_"):
        await send_to_admin(uid)

# ---------------- ADMIN ----------------
async def send_to_admin(uid: int):
    ad = pending_ads[uid]
    text = build_text(ad, admin=True)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_admin_{uid}")],
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"publish_{uid}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{uid}")]
    ])

    if ad.get("photos"):
        await bot.send_media_group(ADMIN_ID, [InputMediaPhoto(media=p) for p in ad["photos"]])
    await bot.send_message(ADMIN_ID, text, reply_markup=kb)

# ---------------- ADMIN ACTIONS ----------------
@dp.callback_query(lambda c: c.data.startswith(("edit_admin_", "publish_", "reject_")))
async def admin_actions(cb: types.CallbackQuery):
    uid = int(cb.data.split("_")[-1])

    if cb.data.startswith("edit_admin_"):
        editing_mode[uid] = "admin"
        ads_data[uid] = {"step": 0, "data": pending_ads[uid]}
        await cb.message.answer("Редактирование объявления")
        await cb.message.answer(FIELDS[0][1])

    elif cb.data.startswith("publish_"):
        ad = pending_ads[uid]
        tags = build_tags(ad)
        if ad.get("photos"):
            await bot.send_media_group(CHANNEL_ID, [InputMediaPhoto(media=p) for p in ad["photos"]])
        msg = await bot.send_message(CHANNEL_ID, build_text(ad) + "\n\n" + tags)
        await bot.send_message(uid, f"Ваше объявление опубликовано:\n{msg.link}")
        pending_ads.pop(uid)

    elif cb.data.startswith("reject_"):
        pending_ads.pop(uid)
        await bot.send_message(uid, "Ваше объявление отклонено")

# ---------------- HELPERS ----------------
def build_text(ad, admin=False):
    return (
        f"🚗 {ad['model']}\n"
        f"📅 {ad['year']}\n"
        f"💰 {ad['price']} ₽\n"
        f"📏 {ad['mileage']} км\n"
        f"📍 Рязань\n"
        f"📞 {ad['contact']}\n"
        f"📝 {ad['description']}"
    )

def build_tags(ad):
    return (
        f"#{ad['model'].replace(' ', '')} "
        f"#{ad['year']} "
        f"#{ad['price']} "
        f"#{ad['mileage']} "
        f"#Рязань"
    )

# ---------------- RUN ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
