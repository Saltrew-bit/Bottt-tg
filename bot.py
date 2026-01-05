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

# ---------- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ----------
def format_ad(ad: dict) -> str:
    return (
        f"🚗 {ad['model']}\n"
        f"📅 {ad['year']}\n"
        f"💰 {ad['price']} ₽\n"
        f"📏 {ad['mileage']} км\n"
        f"📞 {ad['contact']}\n"
        f"📝 {ad['description']}"
    )

# ---------- START ----------
@dp.message(CommandStart())
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🚗 Подать объявление", callback_data="add_ad")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules")]
    ])
    await message.answer("Добро пожаловать в AutoHub62", reply_markup=keyboard)

# ---------- RULES ----------
@dp.callback_query(lambda c: c.data == "rules")
async def rules(cq: types.CallbackQuery):
    await cq.message.answer(
        "📜 Правила:\n"
        "1. Реальная цена\n"
        "2. Контакт обязателен\n"
        "3. До 10 фото"
    )
    await cq.answer()

# ---------- ADD AD ----------
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(cq: types.CallbackQuery):
    ads_data[cq.from_user.id] = {"step": 1, "data": {}}
    await cq.message.answer("Введите марку и модель")
    await cq.answer()

# ---------- FSM ----------
@dp.message()
async def process_steps(msg: types.Message):
    uid = msg.from_user.id
    if uid not in ads_data:
        return

    step = ads_data[uid]["step"]
    ad = ads_data[uid]["data"]

    if step == 1:
        ad["model"] = msg.text
        ads_data[uid]["step"] = 2
        await msg.answer("Введите год")

    elif step == 2:
        ad["year"] = msg.text
        ads_data[uid]["step"] = 3
        await msg.answer("Введите цену")

    elif step == 3:
        ad["price"] = msg.text
        ads_data[uid]["step"] = 4
        await msg.answer("Введите пробег")

    elif step == 4:
        ad["mileage"] = msg.text
        ads_data[uid]["step"] = 5
        await msg.answer("Отправьте фото или 'стоп'")

    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            await msg.answer("Фото принято, можно ещё или 'стоп'")
        elif msg.text.lower() == "стоп":
            ads_data[uid]["step"] = 6
            await msg.answer("Введите контакт")

    elif step == 6:
        ad["contact"] = msg.text
        ads_data[uid]["step"] = 7
        await msg.answer("Введите описание")

    elif step == 7:
        ad["description"] = msg.text
        pending_ads[uid] = ad

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("✅ Отправить на модерацию", callback_data=f"to_moderation_{uid}")],
            [InlineKeyboardButton("❌ Отменить объявление", callback_data=f"cancel_{uid}")]
        ])

        if ad.get("photos"):
            await bot.send_media_group(
                uid,
                [InputMediaPhoto(media=p) for p in ad["photos"]]
            )

        await bot.send_message(uid, "📢 Предпросмотр:\n\n" + format_ad(ad), reply_markup=keyboard)
        del ads_data[uid]

# ---------- CANCEL ----------
@dp.callback_query(lambda c: c.data.startswith("cancel_"))
async def cancel_ad(cq: types.CallbackQuery):
    uid = int(cq.data.split("_")[1])
    pending_ads.pop(uid, None)

    await cq.message.edit_reply_markup()
    await cq.answer("Объявление отменено")

    await bot.send_message(
        uid,
        "Можете подать объявление заново",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton("🚗 Подать объявление", callback_data="add_ad")]]
        )
    )

# ---------- TO MODERATION ----------
@dp.callback_query(lambda c: c.data.startswith("to_moderation_"))
async def to_moderation(cq: types.CallbackQuery):
    uid = int(cq.data.split("_")[1])
    ad = pending_ads.get(uid)
    if not ad:
        await cq.answer("Не найдено")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✅ Опубликовать", callback_data=f"publish_{uid}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"delete_{uid}"),
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_{uid}")
        ]
    ])

    await bot.send_message(ADMIN_ID, "📝 На модерацию:\n\n" + format_ad(ad), reply_markup=keyboard)
    await cq.message.edit_reply_markup()
    await cq.answer("Отправлено")

# ---------- EDIT ----------
@dp.callback_query(lambda c: c.data.startswith("edit_"))
async def edit_ad(cq: types.CallbackQuery):
    uid = int(cq.data.split("_")[1])
    editing_ads[uid] = pending_ads[uid]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🚗 Модель", callback_data=f"edit_field_model_{uid}")],
        [InlineKeyboardButton("📅 Год", callback_data=f"edit_field_year_{uid}")],
        [InlineKeyboardButton("💰 Цена", callback_data=f"edit_field_price_{uid}")],
        [InlineKeyboardButton("📏 Пробег", callback_data=f"edit_field_mileage_{uid}")],
        [InlineKeyboardButton("📞 Контакт", callback_data=f"edit_field_contact_{uid}")],
        [InlineKeyboardButton("📝 Описание", callback_data=f"edit_field_description_{uid}")],
        [InlineKeyboardButton("💾 Сохранить", callback_data=f"save_edit_{uid}")]
    ])

    await cq.message.answer("Выберите поле для редактирования", reply_markup=keyboard)
    await cq.answer()

# ---------- SAVE ----------
@dp.callback_query(lambda c: c.data.startswith("save_edit_"))
async def save_edit(cq: types.CallbackQuery):
    uid = int(cq.data.split("_")[2])
    pending_ads[uid] = editing_ads.pop(uid)

    await cq.answer("Изменения сохранены")
    await bot.send_message(ADMIN_ID, "Обновлённое объявление:\n\n" + format_ad(pending_ads[uid]))

# ---------- PUBLISH / DELETE ----------
@dp.callback_query(lambda c: c.data.startswith(("publish_", "delete_")))
async def admin_action(cq: types.CallbackQuery):
    uid = int(cq.data.split("_")[1])
    ad = pending_ads.pop(uid, None)

    if not ad:
        await cq.answer("Не найдено")
        return

    if cq.data.startswith("publish_"):
        if ad.get("photos"):
            await bot.send_media_group(
                CHANNEL_ID,
                [InputMediaPhoto(media=p) for p in ad["photos"]]
            )
        await bot.send_message(CHANNEL_ID, format_ad(ad))
        await cq.answer("Опубликовано")
    else:
        await cq.answer("Отклонено")

# ---------- RUN ----------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
