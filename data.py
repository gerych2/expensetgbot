# data.py

import json
from datetime import datetime, timedelta

FILENAME = "data.json"
GOALS_FILE = "goals.json"

def load_data():
    try:
        with open(FILENAME, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_data(data_list):
    with open(FILENAME, "w", encoding="utf-8") as f:
        json.dump(data_list, f, indent=4, ensure_ascii=False)

def add_entry(entry_type, amount, description, category="Прочее"):
    data_list = load_data()
    entry = {
        "id": len(data_list) + 1,
        "type": entry_type,
        "amount": amount,
        "description": description,
        "category": category,
        "date": datetime.now().strftime("%d.%m.%Y")
    }
    data_list.append(entry)
    save_data(data_list)

def delete_entry(entry_id):
    data_list = load_data()
    new_data = [entry for entry in data_list if entry["id"] != entry_id]
    for idx, entry in enumerate(new_data, 1):
        entry["id"] = idx
    save_data(new_data)

def get_balance():
    data_list = load_data()
    income = sum(e["amount"] for e in data_list if e["type"] == "income")
    expense = sum(e["amount"] for e in data_list if e["type"] == "expense")
    return income, expense

def list_entries():
    return load_data()

def entries_last_days(days):
    limit_date = datetime.now() - timedelta(days=days)
    return [e for e in load_data() if datetime.strptime(e["date"], "%d.%m.%Y") >= limit_date]

def search_entries(keyword):
    return [e for e in load_data() if keyword.lower() in e["description"].lower()]

# --- Цели накоплений ---
def load_goals():
    try:
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_goals(goals):
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, indent=4, ensure_ascii=False)

def set_goal(name, amount):
    goals = load_goals()
    goals[name] = {"amount": amount}
    save_goals(goals)

def list_goals():
    return load_goals()

def calculate_progress():
    goals = load_goals()
    entries = load_data()
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

def delete_goal(name):
    goals = load_goals()
    if name in goals:
        del goals[name]
        save_goals(goals)

def clear_goals():
    save_goals({})
