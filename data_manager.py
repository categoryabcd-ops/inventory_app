import json
import os
from datetime import datetime

DATA_FILE = "inventory_data.json"

TOTAL_BAGS = 20
TOTAL_BATTERIES = 20
TOTAL_BICYCLES = 10
TOTAL_RAINCOATS = 15
TOTAL_TOOLS = 6

TOOL_NAMES = {
    "1": "Насос",
    "2": "Молоток", 
    "3": "Ключ",
    "4": "Отвертка",
    "5": "Плоскогубцы",
    "6": "Шуруповерт"
}

class DataManager:
    def __init__(self):
        self.data = self.load_data()
    
    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.init_data()
    
    def init_data(self):
        data = {
            "couriers": {},
            "next_courier_id": 1,
            "bags": {},
            "batteries": {},
            "bicycles": {},
            "raincoats": {},
            "tools": {}
        }
        
        for i in range(1, TOTAL_BAGS + 1):
            data["bags"][str(i)] = {"status": "free", "courier": None, "taken_at": None}
        
        for i in range(1, TOTAL_BATTERIES + 1):
            data["batteries"][str(i)] = {"status": "free", "courier": None, "taken_at": None}
        
        for i in range(1, TOTAL_BICYCLES + 1):
            data["bicycles"][str(i)] = {"status": "free", "courier": None, "taken_at": None}
        
        for i in range(1, TOTAL_RAINCOATS + 1):
            data["raincoats"][str(i)] = {"status": "free", "courier": None, "taken_at": None}
        
        for i in range(1, TOTAL_TOOLS + 1):
            data["tools"][str(i)] = {"status": "free", "courier": None, "taken_at": None}
        
        self.save_data(data)
        return data
    
    def save_data(self, data=None):
        if data is None:
            data = self.data
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_couriers(self):
        return {k: v for k, v in self.data["couriers"].items() if v}
    
    def add_courier(self, name):
        name = name.strip()
        if not name:
            return {"success": False, "error": "Имя не может быть пустым"}
        
        for existing in self.data["couriers"].values():
            if existing.lower() == name.lower():
                return {"success": False, "error": f"Курьер '{name}' уже существует"}
        
        courier_id = str(self.data["next_courier_id"])
        self.data["couriers"][courier_id] = name
        self.data["next_courier_id"] += 1
        self.save_data()
        return {"success": True, "courier_id": courier_id, "name": name}
    
    def remove_courier(self, courier_id):
        if courier_id not in self.data["couriers"]:
            return {"success": False, "error": "Курьер не найден"}
        
        courier_name = self.data["couriers"][courier_id]
        
        # Освобождаем все предметы
        for item_type in ["bags", "batteries", "bicycles", "raincoats", "tools"]:
            for num, item in self.data[item_type].items():
                if item.get("courier") == courier_name:
                    self.data[item_type][num] = {"status": "free", "courier": None, "taken_at": None}
        
        del self.data["couriers"][courier_id]
        self.save_data()
        return {"success": True}
    
    def get_free_items(self, item_type):
        free_items = []
        for num, item in self.data[item_type].items():
            if item["status"] == "free":
                free_items.append(num)
        return sorted(free_items, key=int)
    
    def get_taken_items(self, item_type):
        taken_items = []
        for num, item in self.data[item_type].items():
            if item["status"] == "taken":
                taken_items.append({
                    "number": num,
                    "courier": item["courier"],
                    "taken_at": item["taken_at"]
                })
        return taken_items
    
    def give_item(self, item_type, item_num, courier_id):
        if courier_id not in self.data["couriers"]:
            return {"success": False, "error": "Курьер не найден"}
        
        if item_num not in self.data[item_type]:
            return {"success": False, "error": "Предмет не найден"}
        
        if self.data[item_type][item_num]["status"] != "free":
            return {"success": False, "error": "Предмет уже занят"}
        
        courier_name = self.data["couriers"][courier_id]
        
        self.data[item_type][item_num] = {
            "status": "taken",
            "courier": courier_name,
            "taken_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.save_data()
        return {"success": True}
    
    def take_item(self, item_type, item_num, courier_id):
        """Принять предмет обратно (алиас для return_item)"""
        return self.return_item(item_type, item_num, courier_id)
    
    def return_item(self, item_type, item_num, courier_id):
        if courier_id not in self.data["couriers"]:
            return {"success": False, "error": "Курьер не найден"}
        
        if item_num not in self.data[item_type]:
            return {"success": False, "error": "Предмет не найден"}
        
        if self.data[item_type][item_num]["status"] != "taken":
            return {"success": False, "error": "Предмет не занят"}
        
        self.data[item_type][item_num] = {
            "status": "free",
            "courier": None,
            "taken_at": None
        }
        
        self.save_data()
        return {"success": True}
    
    def force_free_item(self, item_type, item_num):
        if item_num not in self.data[item_type]:
            return {"success": False, "error": "Предмет не найден"}
        
        self.data[item_type][item_num] = {
            "status": "free",
            "courier": None,
            "taken_at": None
        }
        
        self.save_data()
        return {"success": True}
    
    def get_all_taken_items(self):
        items = []
        for item_type in ["bags", "batteries", "bicycles", "raincoats", "tools"]:
            for num, item in self.data[item_type].items():
                if item["status"] == "taken" and item["courier"]:
                    taken_at = item["taken_at"]
                    if taken_at:
                        taken_dt = datetime.fromisoformat(taken_at)
                        hours_ago = (datetime.now() - taken_dt).total_seconds() / 3600
                        time_str = f"{hours_ago:.1f} ч назад"
                    else:
                        time_str = "время не указано"
                    
                    items.append({
                        "type": item_type,
                        "type_display": self.get_type_display(item_type),
                        "number": num,
                        "courier": item["courier"],
                        "taken_at": taken_at,
                        "time_ago": time_str,
                        "tool_name": TOOL_NAMES.get(num) if item_type == "tools" else None
                    })
        return items
    
    def get_type_display(self, item_type):
        types = {
            "bags": "🎒 Сумка",
            "batteries": "🔋 Аккумулятор",
            "bicycles": "🚲 Велосипед",
            "raincoats": "🌧️ Дождевик",
            "tools": "🛠️ Инструмент"
        }
        return types.get(item_type, item_type)
    
    def get_stats(self):
        stats = {}
        for item_type in ["bags", "batteries", "bicycles", "raincoats", "tools"]:
            total = len(self.data[item_type])
            taken = sum(1 for item in self.data[item_type].values() if item["status"] == "taken")
            free = total - taken
            percent = int((taken / total) * 100) if total > 0 else 0
            stats[item_type] = {
                "total": total,
                "taken": taken,
                "free": free,
                "percent": percent
            }
        return stats