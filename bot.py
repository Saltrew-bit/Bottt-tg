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

# --- Старт ---
@dp.message(CommandStart())
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("🚗 Подать объявление", callback_data="add_ad")],
            [InlineKeyboardButton("📜 Правила", callback_data="rules")],
            [InlineKeyboardButton("👨‍💼 Связь с админом", url="https://t.me/saltrew")]
        ]
    )

    await message.answer(
        "👋 Здравствуйте!\n\n"
        "Я бот канала AutoHub62.\n"
        "Помогаю размещать объявления о продаже авто.\n\n"
        "Выберите действие ⬇️",
        reply_markup=keyboard
    )

# --- Правила ---
@dp.callback_query(lambda c: c.data == "rules")
async def rules(cq: types.CallbackQuery):
    await cq.message.answer(
        "📜 Правила:\n"
        "• Реальная цена\n"
        "• Контакт обязателен\n"
        "• До 10 фото\n"
        "• Авто Рязань/область"
    )
    await cq.answer()

# --- Начать объявление ---
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(cq: types.CallbackQuery):
    ads_data[cq.from_user.id] = {"step": 1, "data": {}}
    await cq.message.answer("Введите марку и модель автомобиля:")
    await cq.answer()

# --- ЕДИНЫЙ обработчик сообщений ---
@dp.message()
async def process_message(msg: types.Message):
    user_id = msg.from_user.id
    if user_id not in ads_data:
        return

    step = ads_data[user_id]["step"]
    ad = ads_data[user_id]["data"]

    # --- РЕДАКТИРОВАНИЕ АДМИНОМ ---
    if isinstance(step, str) and step.startswith("edit_"):
        field = step.replace("edit_", "")
        ad[field] = msg.text

        await msg.answer(f"Поле «{field}» обновлено.")
        await send_preview_admin(user_id)

        del ads_data[user_id]
        return

    # --- ШАГИ ПОДАЧИ ---
    if step == 1:
        ad["model"] = msg.text
        ads_data[user_id]["step"] = 2
        await msg.answer("Введите год выпуска:")

    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("Введите год цифрами.")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("Введите цену:")

    elif step == 3:
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("Введите пробег (км):")

    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer("Введите пробег цифрами.")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer("Отправьте фото (до 10). Напишите «стоп» для завершения.")

    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            await msg.answer(f"Фото принято ({len(ad['photos'])}/10)")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer("Введите контакт:")
        else:
            await msg.answer("Отправьте фото или «стоп».")

    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer("Введите описание:")

    elif step == 7:
        ad["description"] = msg.text
        pending_ads[user_id] = ad

        text = (
            f"🚗 {ad['model']}\n"
            f"📅 {ad['year']}\n"
            f"💰 {ad['price']}\n"
            f"📏 {ad['mileage']} км\n"
            f"📞 {ad['contact']}\n"
            f"📝 {ad['description']}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("✅ Отправить на модерацию", callback_data=f"to_moderation_{user_id}")],
            [InlineKeyboardButton("❌ Отменить объявление", callback_data=f"cancel_{user_id}")]
        ])

        await msg.answer(text, reply_markup=keyboard)
        del ads_data[user_id]

# --- CALLBACK: модерация ---
@dp.callback_query(lambda c: c.data.startswith(("to_moderation_", "cancel_", "edit_")))
async def moderation(cq: types.CallbackQuery):
    data = cq.data
    user_id = int(data.split("_")[1])

    if data.startswith("to_moderation_"):
        ad = pending_ads[user_id]

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton("✅ Опубликовать", callback_data=f"publish_{user_id}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"delete_{user_id}"),
                InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_{user_id}")
            ]
        ])

        await bot.send_message(ADMIN_ID, format_ad(ad), reply_markup=keyboard)
        await cq.message.edit_reply_markup()
        await cq.answer("Отправлено на модерацию")

    elif data.startswith("cancel_"):
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление отменено")

        await bot.send_message(
            user_id,
            "Подать объявление заново ⬇️",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton("🚗 Подать объявление", callback_data="add_ad")]]
            )
        )

    elif data.startswith("edit_"):
        editing_ads[user_id] = pending_ads[user_id]

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("🚗 Марка/Модель", callback_data=f"edit_field_model_{user_id}")],
            [InlineKeyboardButton("📅 Год", callback_data=f"edit_field_year_{user_id}")],
            [InlineKeyboardButton("💰 Цена", callback_data=f"edit_field_price_{user_id}")],
            [InlineKeyboardButton("📏 Пробег", callback_data=f"edit_field_mileage_{user_id}")],
            [InlineKeyboardButton("📞 Контакт", callback_data=f"edit_field_contact_{user_id}")],
            [InlineKeyboardButton("📝 Описание", callback_data=f"edit_field_description_{user_id}")],
            [InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_edit_{user_id}")]
        ])

        await cq.message.answer("Выберите поле:", reply_markup=keyboard)
        await cq.answer()

# --- Выбор поля ---
@dp.callback_query(lambda c: c.data.startswith("edit_field_"))
async def edit_field(cq: types.CallbackQuery):
    _, _, field, user_id = cq.data.split("_")
    user_id = int(user_id)

    ads_data[cq.from_user.id] = {
        "step": f"edit_{field}",
        "data": editing_ads[user_id]
    }

    await cq.message.answer(f"Введите новое значение для «{field}»:")
    await cq.answer()

# --- Сохранить / отменить редактирование ---
@dp.callback_query(lambda c: c.data.startswith(("save_edit_", "cancel_edit_")))
async def save_cancel(cq: types.CallbackQuery):
    user_id = int(cq.data.split("_")[2])

    if cq.data.startswith("save_edit_"):
        pending_ads[user_id] = editing_ads.pop(user_id)
        await cq.answer("Изменения сохранены")

    else:
        editing_ads.pop(user_id, None)
        await cq.answer("Редактирование отменено")

# --- Публикация ---
@dp.callback_query(lambda c: c.data.startswith(("publish_", "delete_")))
async def publish(cq: types.CallbackQuery):
    user_id = int(cq.data.split("_")[1])

    if cq.data.startswith("publish_"):
        ad = pending_ads.pop(user_id)
        await bot.send_message(CHANNEL_ID, format_ad(ad))
        await cq.answer("Опубликовано")

    else:
        pending_ads.pop(user_id, None)
        await cq.answer("Удалено")

# --- Вспомогательные ---
def format_ad(ad: dict) -> str:
    return (
        f"🚗 {ad['model']}\n"
        f"📅 {ad['year']}\n"
        f"💰 {ad['price']}\n"
        f"📏 {ad['mileage']} км\n"
        f"📞 {ad['contact']}\n"
        f"📝 {ad['description']}"
    )

async def send_preview_admin(user_id: int):
    ad = editing_ads[user_id]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("💾 Сохранить", callback_data=f"save_edit_{user_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_edit_{user_id}")]
    ])
    await bot.send_message(ADMIN_ID, format_ad(ad), reply_markup=keyboard)

# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
