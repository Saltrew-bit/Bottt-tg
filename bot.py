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
        await msg.answer("Введите год выпуска автомобиля:")

    elif step == 2:
        if not msg.text.isdigit():
            await msg.answer("❌ Введите год выпуска цифрами, например: 2015")
            return
        ad["year"] = msg.text
        ads_data[user_id]["step"] = 3
        await msg.answer("Введите цену автомобиля (₽):")

    elif step == 3:
        if not msg.text.replace(" ", "").isdigit():
            await msg.answer("❌ Введите цену цифрами, например: 350000")
            return
        ad["price"] = msg.text
        ads_data[user_id]["step"] = 4
        await msg.answer("Введите пробег автомобиля (км):")

    elif step == 4:
        if not msg.text.replace(" ", "").isdigit():
            await msg.answer("❌ Введите пробег цифрами, например: 120000")
            return
        ad["mileage"] = msg.text
        ads_data[user_id]["step"] = 5
        await msg.answer("Добавьте описание автомобиля:")

    elif step == 5:
        ad["description"] = msg.text
        ads_data[user_id]["step"] = 6
        await msg.answer("Отправьте фото автомобиля (до 10 шт.). Когда закончите, напишите 'стоп'.")

    elif step == 6:
        if msg.photo:
            ad.setdefault("photos", []).append(msg.photo[-1].file_id)
            if len(ad["photos"]) < 10:
                await msg.answer(f"Фото принято ({len(ad['photos'])}/10). Можете прислать ещё или напишите 'стоп'.")
            else:
                ads_data[user_id]["step"] = 7
                await msg.answer("Фото завершены. Введите контакт:")
        elif msg.text.lower() == "стоп":
            ads_data[user_id]["step"] = 7
            await msg.answer("Фото завершены. Введите контакт:")
        else:
            await msg.answer("Отправьте фото или напишите 'стоп'.")

    elif step == 7:
        ad["contact"] = msg.text
        ads_data[user_id]["step"] = 8

        text = (
            f"Новое объявление от {msg.from_user.full_name}:\n\n"
            f"🚗 Модель: {ad['model']}\n"
            f"📅 Год выпуска: {ad['year']}\n"
            f"💰 Цена: {ad['price']} ₽\n"
            f"📏 Пробег: {ad['mileage']} км\n"
            f"📝 Описание: {ad['description']}\n"
            f"📞 Контакт: {ad['contact']}"
        )

        media = [InputMediaPhoto(pid) for pid in ad.get("photos", [])]
        pending_ads[user_id] = ad

        if media:
            await bot.send_media_group(ADMIN_ID, media)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("✅ Опубликовать в канал", callback_data=f"publish_{user_id}")],
            [InlineKeyboardButton("❌ Удалить объявление", callback_data=f"delete_{user_id}")]
        ])
        await bot.send_message(ADMIN_ID, text, reply_markup=keyboard)
        await msg.answer("✅ Ваше объявление принято и отправлено на модерацию!")
        del ads_data[user_id]
