from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import json
import uvicorn

# Файл, в котором хранятся правила начисления бонусов
RULES_FILE = "rules.json"

# Функция для загрузки правил из JSON-файла
def load_rules():
    with open(RULES_FILE, "r") as f:
        return json.load(f)

# Загружаем правила при запуске
RULES = load_rules()

# Инициализация FastAPI
app = FastAPI()

# Определяем структуру запроса
class BonusRequest(BaseModel):
    transaction_amount: float  # Сумма покупки
    timestamp: str  # Временная метка покупки
    customer_status: str  # Статус клиента (обычный или VIP)

# Функция для парсинга временной метки
def parse_datetime(timestamp: str):
    try:
        # Преобразуем ISO 8601 строку в объект datetime, корректируя Z на +00:00
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Invalid timestamp format. Use ISO 8601.")

# Функция для расчета бонусов
def calculate_bonus(amount: float, timestamp: str, status: str):
    dt = parse_datetime(timestamp)  # Преобразуем время покупки в объект datetime
    applied_rules = []  # Список применённых правил
    rules = load_rules()  # Загружаем актуальные правила
    
    # Базовое начисление бонусов
    base_bonus = amount // rules["base"]["per_dollars"] * rules["base"]["bonus"]
    total_bonus = base_bonus
    applied_rules.append({"rule": "base rate", "bonus": round(base_bonus)})
    
    # Применяем дополнительные правила
    for rule in sorted(rules["additional"], key=lambda r: r["order"]):
        if rule["type"] == "weekend" and dt.weekday() in [5, 6]:  # Проверяем выходной день
            bonus = total_bonus * rule["multiplier"] - total_bonus
            total_bonus += bonus
            applied_rules.append({"rule": rule["name"], "bonus": round(bonus)})
        elif rule["type"] == "vip" and status == "vip":  # Проверяем VIP-статус
            bonus = total_bonus * rule["multiplier"] - total_bonus
            total_bonus += bonus
            applied_rules.append({"rule": rule["name"], "bonus": round(bonus)})
    
    return {"total bonus": round(total_bonus), "applied rules": applied_rules}

# Обработчик POST-запроса для расчета бонусов
@app.post("/calculate-bonus")
def calculate_bonus_api(request: BonusRequest):
    return calculate_bonus(request.transaction_amount, request.timestamp, request.customer_status)

# Запуск FastAPI сервера
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
