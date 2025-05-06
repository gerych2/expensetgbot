import os
import json
from datetime import datetime, timedelta

DATA_FILE = "data/data.json"
GOALS_FILE = "data/goals.json"

os.makedirs("data", exist_ok=True)

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_entry(user_id, entry_type, amount, description, category="Прочее"):
    data = load_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = []
    entry = {
        "id": len(data[user_id]) + 1,
        "type": entry_type,
        "amount": amount,
        "description": description,
        "category": category,
        "date": datetime.now().strftime("%d.%m.%Y")
    }
    data[user_id].append(entry)
    save_data(data)

def delete_entry(user_id, entry_id):
    data = load_data()
    user_id = str(user_id)
    if user_id in data:
        data[user_id] = [e for e in data[user_id] if e["id"] != entry_id]
        for idx, entry in enumerate(data[user_id], 1):
            entry["id"] = idx
    save_data(data)

def get_balance(user_id):
    data = load_data()
    user_data = data.get(str(user_id), [])
    income = sum(e["amount"] for e in user_data if e["type"] == "income")
    expense = sum(e["amount"] for e in user_data if e["type"] == "expense")
    return income, expense

def list_entries(user_id):
    return load_data().get(str(user_id), [])

def entries_last_days(user_id, days):
    limit_date = datetime.now() - timedelta(days=days)
    return [e for e in list_entries(user_id) if datetime.strptime(e["date"], "%d.%m.%Y") >= limit_date]

def search_entries(user_id, keyword):
    return [e for e in list_entries(user_id) if keyword.lower() in e["description"].lower()]

def load_goals():
    try:
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_goals(goals):
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, indent=4, ensure_ascii=False)

def set_goal(user_id, name, amount):
    goals = load_goals()
    user_id = str(user_id)
    if user_id not in goals:
        goals[user_id] = {}
    goals[user_id][name] = {"amount": amount}
    save_goals(goals)

def list_goals(user_id):
    return load_goals().get(str(user_id), {})

def calculate_progress(user_id):
    goals = list_goals(user_id)
    entries = list_entries(user_id)
    income_total = sum(e["amount"] for e in entries if e["type"] == "income")
    expense_total = sum(e["amount"] for e in entries if e["type"] == "expense")
    net_savings = income_total - expense_total

    result = {}
    for name, info in goals.items():
        goal_amount = info["amount"]
        progress = min((net_savings / goal_amount) * 100, 100) if goal_amount > 0 else 0
        result[name] = {
            "target": goal_amount,
            "progress": max(net_savings, 0),
            "percent": round(progress, 1)
        }
    return result
