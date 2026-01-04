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

# --- Красивое оформление шага ---
def step_card(title, content, example=None, warning=None, emoji="📌"):
    msg = f"{emoji} *{title}*\n{content}"
    if example:
        msg += f"\n💡 _Пример_: `{example}`"
    if warning:
        msg += f"\n❌ {warning}"
    return msg

# --- Стартовое приветствие ---
@dp.message(CommandStart())
async def start(message: types.Message):
    if message.chat.type == "private":
        try:
            await message.delete()
        except Exception:
            pass

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("🚗 Подать объявление", callback_data="add_ad")],
            [InlineKeyboardButton("📜 Правила", callback_data="rules")],
            [InlineKeyboardButton("👨‍💼 Связь с админом", url="https://t.me/saltrew")]
        ]
    )

    await message.answer(
        step_card("Добро пожаловать!", 
                  "Я бот канала *AutoHub62*.\nПомогаю удобно размещать объявления о продаже авто.\nВыберите действие ниже ⬇️", 
                  emoji="👋"),
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# --- Правила ---
@dp.callback_query(lambda c: c.data == "rules")
async def rules(callback: types.CallbackQuery):
    await callback.message.answer(
        step_card(
            "Правила размещения объявлений",
            "✅ Авто реально в Рязани или области\n"
            "✅ Указывайте реальную цену\n"
            "✅ Контакт обязателен\n"
            "✅ Добавьте актуальные фото\n"
            "✅ Краткое и информативное описание",
            warning="Объявления, не соответствующие правилам, не публикуются.",
            emoji="📜"
        ),
        parse_mode="Markdown"
    )

# --- Начало подачи объявления ---
@dp.callback_query(lambda c: c.data == "add_ad")
async def add_ad(callback: types.CallbackQuery):
    ads_data[callback.from_user.id] = {"step": 1, "data": {}}
    await callback.message.answer(
        step_card("Шаг 1: Марка и модель", "Введите марку и модель автомобиля", example="Toyota Camry", emoji="🚗"),
        parse_mode="Markdown"
    )

# --- Обработка сообщений по шагам ---
@dp.message()
async def process_message(msg: types.Message):
    user_id = msg.from_user.id
    if user_id not in ads_data:
        return

    step = ads_data[user_id]["step"]
    ad = ads_data[user_id]["data"]

    if step == 1:
        ad["model"] = msg.text
        ads_data[user_id]["step"] = 2
        await msg.answer(step_card("Шаг 2: Год выпуска", "Введите год автомобиля", example="2015", emoji="📅"), parse_mode="Markdown")

    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer(step_card("Ошибка", "Год должен быть числом", warning="Введите только цифры для года выпуска", emoji="❌"))
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer(step_card("Шаг 3: Цена", "Введите стоимость автомобиля", example="450.000", emoji="💰"), parse_mode="Markdown")

    elif step == 3:
        if not msg.text.replace(".", "").isdigit():
            await msg.answer(step_card("Ошибка", "Цена должна быть числом", warning="Точку можно использовать как разделитель", emoji="❌"))
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer(step_card("Шаг 4: Пробег", "Введите пробег автомобиля в км", example="120000", emoji="📏"), parse_mode="Markdown")

    elif step == 4:
        if not msg.text.isdigit():
            await msg.answer(step_card("Ошибка", "Пробег должен быть числом", warning="Введите только цифры", emoji="❌"))
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer(step_card("Шаг 5: Фотографии", "Отправьте до 10 фото автомобиля. Когда закончите, напишите 'стоп'", emoji="📸"), parse_mode="Markdown")

    elif step == 5:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"✅ Фото принято ({len(ad['photos'])}/10). Отправьте ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 6
                await msg.answer(step_card("Готово!", "Все фото получены. Введите контакт:", emoji="📞"), parse_mode="Markdown")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 6
            await msg.answer(step_card("Готово!", "Все фото получены. Введите контакт:", emoji="📞"), parse_mode="Markdown)
        else:
            await msg.answer(step_card("Ошибка", "Отправьте фото или напишите 'стоп'", emoji="❌"))

    elif step == 6:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 7
        await msg.answer(step_card("Шаг 6: Контакт", "Введите номер телефона или Telegram", example="+7 900 123-45-67 или @username", emoji="📞"), parse_mode="Markdown")

    elif step == 7:
        ad["description"] = msg.text
        pending_ads[user_id] = ad

        # --- Предпросмотр объявления ---
        text_preview = (
            f"📋 *Предпросмотр объявления*\n\n"
            f"🚗 *Модель*: {ad['model']}\n"
            f"📅 *Год*: {ad['year']}\n"
            f"💰 *Цена*: {ad['price']} ₽\n"
            f"📏 *Пробег*: {ad['mileage']} км\n"
            f"📞 *Контакт*: {ad['contact']}\n"
            f"📝 *Описание*: {ad['description']}\n\n"
            f"После проверки администратором объявление будет опубликовано в канале."
        )

        media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Отправить на модерацию", callback_data=f"publish_{user_id}")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data=f"delete_{user_id}")]
            ]
        )

        if media:
            await bot.send_media_group(chat_id=ADMIN_ID, media=media)

        await bot.send_message(chat_id=ADMIN_ID, text=text_preview, reply_markup=keyboard, parse_mode="Markdown")
        await msg.answer(step_card("Готово!", "Объявление отправлено на модерацию!", emoji="🎉"), parse_mode="Markdown")
        del ads_data[user_id]

# --- Действия админа ---
@dp.callback_query(lambda c: c.data.startswith("publish_") or c.data.startswith("delete_"))
async def handle_admin_actions(cq: types.CallbackQuery):
    if cq.from_user.id != ADMIN_ID:
        await cq.answer("Только админ может управлять объявлениями.")
        return

    data = cq.data
    user_id = int(data.split("_")[1])
    if data.startswith("publish_"):
        ad = pending_ads.get(user_id)
        if ad:
            text = (
                f"🚗 {ad['model']}\n"
                f"📅 {ad['year']}\n"
                f"💰 {ad['price']} ₽\n"
                f"📏 {ad['mileage']} км\n"
                f"📞 {ad['contact']}\n"
                f"📝 {ad['description']}"
            )
            media = [InputMediaPhoto(media=pid) for pid in ad.get("photos", [])]
            if media:
                await bot.send_media_group(chat_id=CHANNEL_ID, media=media)
            await bot.send_message(chat_id=CHANNEL_ID, text=text)
            del pending_ads[user_id]
            await cq.message.edit_reply_markup()
            await cq.answer("Объявление опубликовано!")
        else:
            await cq.answer("Объявление не найдено.")
    elif data.startswith("delete_"):
        pending_ads.pop(user_id, None)
        await cq.message.edit_reply_markup()
        await cq.answer("Объявление удалено.")

# --- Запуск бота ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
