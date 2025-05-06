import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.default import DefaultBotProperties
from services.config import TOKEN
from services.settings import PIN_CODE
from services import data, tips

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

user_access = set()
user_modes = {}
user_temp_data = {}
awaiting_description = {}

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Доход"), KeyboardButton(text="➖ Расход")],
        [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="📋 Операции")],
        [KeyboardButton(text="📅 Отчёт"), KeyboardButton(text="🎯 Цель")],
        [KeyboardButton(text="📈 Прогресс"), KeyboardButton(text="🗑️ Удалить операцию")],
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
    user_id = str(message.from_user.id)
    text = message.text.strip()

    if user_id not in user_access:
        if text == PIN_CODE:
            user_access.add(user_id)
            await message.answer("✅ Доступ разрешён! Выберите действие:", reply_markup=main_keyboard)
        else:
            await message.answer("❌ Неверный PIN-код. Попробуйте снова:")
        return

    if text == "🚪 Выход":
        user_access.discard(user_id)
        await message.answer("🚪 Вы вышли из бота. Введите PIN-код для входа снова.")
        return

    if text == "➕ Доход":
        user_modes[user_id] = "income"
        await message.answer("Введите сумму и описание дохода через запятую:\n<code>5000, зарплата</code>")
        return

    if text == "➖ Расход":
        user_modes[user_id] = "expense"
        await message.answer("Введите сумму и описание расхода через запятую:\n<code>200, продукты</code>")
        return

    if text == "💰 Баланс":
        income, expense = data.get_balance(user_id)
        await message.answer(f"<b>💰 Баланс:</b>\nДоходов: {income} ₽\nРасходов: {expense} ₽\nИтого: {income - expense} ₽")
        return

    if text == "📋 Операции":
        entries = data.list_entries(user_id)
        if not entries:
            await message.answer("⚠️ Нет операций.")
        else:
            msg = "<b>📋 Операции:</b>\n\n"
            for e in entries:
                icon = "💵" if e["type"] == "income" else "🧾"
                msg += f"{icon} #{e['id']} — {e['amount']} ₽ — {e['description']} ({e['category']}, {e['date']})\n"
            await message.answer(msg)
        return

    if text == "📅 Отчёт":
        week = data.entries_last_days(user_id, 7)
        month = data.entries_last_days(user_id, 30)
        w = sum(e["amount"] for e in week if e["type"] == "expense")
        m = sum(e["amount"] for e in month if e["type"] == "expense")
        await message.answer(f"📅 Расходы:\nЗа 7 дней: {w} ₽\nЗа 30 дней: {m} ₽")
        return

    if text == "🎯 Цель":
        user_modes[user_id] = "goal_add"
        await message.answer("Введите цель в формате:\n<code>На отпуск, 10000</code>")
        return

    if text == "📈 Прогресс":
        goals = data.calculate_progress(user_id)
        if not goals:
            await message.answer("🎯 Целей нет.")
        else:
            msg = "<b>📈 Прогресс по целям:</b>\n\n"
            for name, info in goals.items():
                msg += f"🔹 {name}: {info['progress']} ₽ / {info['target']} ₽ ({info['percent']}%)\n"
            await message.answer(msg)
        return

    if text == "🗑️ Удалить операцию":
        user_modes[user_id] = "delete"
        await message.answer("Введите номер операции для удаления:")
        return

    if text == "💡 Совет":
        await message.answer(f"💡 {tips.random_tip()}")
        return

    if user_id in user_modes:
        mode = user_modes[user_id]
        if mode == "income":
            try:
                amount_str, description = text.split(",", 1)
                amount = float(amount_str.strip())
                description = description.strip()
                data.add_entry(user_id, "income", amount, description, "Доход")
                await message.answer("✅ Доход добавлен.", reply_markup=main_keyboard)
                del user_modes[user_id]
            except:
                await message.answer("⚠️ Неверный формат! Пример:\n<code>5000, зарплата</code>")
            return
        if mode == "expense":
            try:
                amount_str, description = text.split(",", 1)
                amount = float(amount_str.strip())
                description = description.strip()
                user_temp_data[user_id] = {"amount": amount, "description": description}
                await message.answer("Выберите категорию:", reply_markup=categories_keyboard)
                del user_modes[user_id]
            except:
                await message.answer("⚠️ Неверный формат! Пример:\n<code>200, продукты</code>")
            return
        if mode == "goal_add":
            try:
                name, amount_str = text.split(",", 1)
                name = name.strip()
                amount = float(amount_str.strip())
                data.set_goal(user_id, name, amount)
                await message.answer(f"🎯 Цель '{name}' добавлена.", reply_markup=main_keyboard)
                del user_modes[user_id]
            except:
                await message.answer("⚠️ Неверный формат! Пример:\n<code>На отпуск, 10000</code>")
            return
        if mode == "delete":
            try:
                op_id = int(text.strip())
                data.delete_entry(user_id, op_id)
                await message.answer(f"🗑️ Операция #{op_id} удалена.")
                del user_modes[user_id]
            except:
                await message.answer("⚠️ Неверный номер.")
            return

    if user_id in user_temp_data:
        entry = user_temp_data[user_id]
        if text == "📦 Прочее":
            awaiting_description[user_id] = entry
            await message.answer("Введите описание:")
            del user_temp_data[user_id]
        else:
            category = text.replace("🍔 ", "").replace("🚌 ", "").replace("🏠 ", "").replace("👕 ", "").replace("🎉 ", "").strip()
            data.add_entry(user_id, "expense", entry["amount"], entry["description"], category=category)
            await message.answer("✅ Расход добавлен.", reply_markup=main_keyboard)
            del user_temp_data[user_id]
        return

    if user_id in awaiting_description:
        entry = awaiting_description[user_id]
        data.add_entry(user_id, "expense", entry["amount"], text, category="Прочее")
        await message.answer("✅ Расход добавлен.", reply_markup=main_keyboard)
        del awaiting_description[user_id]

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
