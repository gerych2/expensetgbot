# bot.py

import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.default import DefaultBotProperties
from config import TOKEN
import data
import tips

PIN_CODE = "1234"  # пароль входа

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

user_modes = {}
user_temp_data = {}
awaiting_description = {}
user_access = set()

# Клавиатура
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Доход"), KeyboardButton(text="➖ Расход")],
        [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="📋 Операции")],
        [KeyboardButton(text="📅 Отчёт"), KeyboardButton(text="🔎 Поиск")],
        [KeyboardButton(text="🎯 Цель"), KeyboardButton(text="📈 Прогресс")],
        [KeyboardButton(text="🗑️ Удалить операцию"), KeyboardButton(text="🗑️ Удалить цель")],
        [KeyboardButton(text="💡 Совет"), KeyboardButton(text="🚪 Выход")]
    ],
    resize_keyboard=True
)

categories_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🍔 Еда"), KeyboardButton(text="🚌 Транспорт")],
        [KeyboardButton(text="🏠 Жильё"), KeyboardButton(text="👕 Одежда")],
        [KeyboardButton(text="🎉 Развлечения"), KeyboardButton(text="📦 Прочее")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🔒 Введите PIN-код для доступа:")

@dp.message()
async def all_messages(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # --- Вход по PIN-коду ---
    if user_id not in user_access:
        if text == PIN_CODE:
            user_access.add(user_id)
            await message.answer("✅ Доступ разрешён!", reply_markup=main_keyboard)
        else:
            await message.answer("❌ Неверный PIN. Попробуйте снова.")
        return

    # --- Выход ---
    if text == "🚪 Выход":
        user_access.discard(user_id)
        await message.answer("🚪 Вы вышли. Введите /start для входа.")
        return

    # --- Команды кнопок ---
    if text == "➕ Доход":
        user_modes[user_id] = "income"
        await message.answer("Введите сумму и описание через запятую:\n<code>5000, зарплата</code>")
        return

    if text == "➖ Расход":
        user_modes[user_id] = "expense"
        await message.answer("Введите сумму и описание через запятую:\n<code>200, продукты</code>")
        return

    if text == "💰 Баланс":
        income, expense = data.get_balance()
        await message.answer(f"<b>💰 Баланс:</b>\nДоходы: {income} ₽\nРасходы: {expense} ₽\nИтого: {income - expense} ₽")
        return

    if text == "📋 Операции":
        entries = data.list_entries()
        if not entries:
            await message.answer("⚠️ Операций пока нет.")
        else:
            msg = "<b>📋 Операции:</b>\n"
            for e in entries:
                icon = "💵" if e["type"] == "income" else "🧾"
                msg += f"{icon} #{e['id']}: {e['amount']} ₽ — {e['description']} ({e['category']}, {e['date']})\n"
            await message.answer(msg)
        return

    if text == "📅 Отчёт":
        week = data.entries_last_days(7)
        month = data.entries_last_days(30)
        w = sum(e["amount"] for e in week if e["type"] == "expense")
        m = sum(e["amount"] for e in month if e["type"] == "expense")
        await message.answer(f"📅 За 7 дней: {w} ₽\n📅 За 30 дней: {m} ₽")
        return

    if text == "🎯 Цель":
        user_modes[user_id] = "goal_add"
        await message.answer("Введите цель в формате:\n<code>На отпуск, 10000</code>")
        return

    if text == "🗑️ Удалить цель":
        data.clear_goals()
        await message.answer("🗑️ Все цели удалены.")
        return

    if text == "📈 Прогресс":
        goals = data.calculate_progress()
        if not goals:
            await message.answer("🎯 Целей нет.")
        else:
            msg = "<b>📈 Прогресс:</b>\n"
            for name, info in goals.items():
                msg += f"🔹 {name}: {info['progress']} / {info['target']} ₽ ({info['percent']}%)\n"
            await message.answer(msg)
        return

    if text == "🗑️ Удалить операцию":
        user_modes[user_id] = "delete"
        await message.answer("Введите номер операции, которую хотите удалить:")
        return

    if text == "💡 Совет":
        await message.answer(f"💡 {tips.random_tip()}")
        return

    if text == "🔎 Поиск":
        await message.answer("Введите ключевое слово для поиска:")
        return

    # --- Режимы ---
    if user_id in user_modes:
        mode = user_modes[user_id]

        if mode in ["income", "expense"]:
            parts = text.split(",", 1)
            if len(parts) < 2:
                await message.answer("⚠️ Неверный формат. Пример:\n<code>5000, зарплата</code>")
                return
            try:
                amount = float(parts[0].strip())
                description = parts[1].strip()
                if mode == "income":
                    data.add_entry("income", amount, description, category="Доход")
                    await message.answer("✅ Доход добавлен.", reply_markup=main_keyboard)
                    del user_modes[user_id]
                else:
                    user_temp_data[user_id] = {"amount": amount, "description": description}
                    await message.answer("Выберите категорию расхода:", reply_markup=categories_keyboard)
                    del user_modes[user_id]
            except:
                await message.answer("⚠️ Ошибка ввода.")
            return

        if mode == "goal_add":
            try:
                name, amount_str = text.split(",", 1)
                name = name.strip()
                amount = float(amount_str.strip())
                data.set_goal(name, amount)
                await message.answer(f"🎯 Цель '{name}' на {amount} ₽ добавлена.", reply_markup=main_keyboard)
                del user_modes[user_id]
            except:
                await message.answer("⚠️ Пример: <code>На отпуск, 10000</code>")
            return

        if mode == "delete":
            try:
                entry_id = int(text)
                data.delete_entry(entry_id)
                await message.answer(f"🗑️ Операция #{entry_id} удалена.", reply_markup=main_keyboard)
                del user_modes[user_id]
            except:
                await message.answer("⚠️ Введите номер операции.")
            return

    # --- Расход: категория ---
    if user_id in user_temp_data:
        entry = user_temp_data[user_id]
        category = text.replace("🍔 ", "").replace("🚌 ", "").replace("🏠 ", "").replace("👕 ", "").replace("🎉 ", "").replace("📦 ", "").strip()
        data.add_entry("expense", entry["amount"], entry["description"], category=category)
        await message.answer("✅ Расход добавлен.", reply_markup=main_keyboard)
        del user_temp_data[user_id]
        return

    # --- Поиск по ключевому слову ---
    results = data.search_entries(text)
    if results:
        msg = "<b>🔎 Найденные операции:</b>\n\n"
        for e in results:
            msg += f"{e['id']}: {e['amount']} ₽ — {e['description']} ({e['category']}, {e['date']})\n"
        await message.answer(msg)
    else:
        await message.answer("❌ Ничего не найдено.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
