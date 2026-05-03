from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
import socket

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Файл для хранения данных торговых точек
SHOPS_FILE = "shops_data.json"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def load_shops():
    """Загрузить данные всех торговых точек"""
    if os.path.exists(SHOPS_FILE):
        with open(SHOPS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Создаём 7 торговых точек
    shops = {}
    shop_names = ["Центральная", "Северная", "Южная", "Восточная", "Западная", "Привокзальная", "ТРЦ"]
    
    # Количество предметов каждого типа в каждой точке
    totals = {
        "bags": 20,
        "batteries": 20,
        "bicycles": 10,
        "raincoats": 15,
        "tools": 6
    }
    
    for i in range(1, 8):
        # Инвентарь точки
        inventory = {}
        for item_type, total in totals.items():
            inventory[item_type] = {}
            for num in range(1, total + 1):
                inventory[item_type][str(num)] = {
                    "status": "free",
                    "courier": None,
                    "taken_at": None
                }
        
        # Курьеры точки (для инвентаря)
        shop_couriers = {}
        
        # График работы точки (7 районов)
        schedule_regions = {}
        region_names = ["Район 1", "Район 2", "Район 3", "Район 4", "Район 5", "Район 6", "Район 7"]
        for r in range(1, 8):
            schedule_regions[str(r)] = {
                "name": region_names[r-1],
                "couriers": {},
                "statuses": {}
            }
        
        shops[str(i)] = {
            "id": str(i),
            "name": f"Торговая точка {i} - {shop_names[i-1]}",
            "inventory": inventory,
            "inventory_couriers": shop_couriers,
            "schedule": schedule_regions
        }
    
    save_shops(shops)
    return shops

def save_shops(data):
    with open(SHOPS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============ WebSocket события ============
@socketio.on('connect')
def handle_connect():
    print(f'✅ Клиент подключился: {request.sid}')

# События для инвентаря
@socketio.on('inventory_update')
def handle_inventory_update(data):
    try:
        shops_data = load_shops()
        shop_id = str(data.get('shop_id'))
        action = data.get('action')
        item_type = data.get('item_type')
        item_num = str(data.get('item_num'))
        
        if shop_id not in shops_data:
            return
        
        if action == 'give':
            if item_num in shops_data[shop_id]['inventory'][item_type]:
                if shops_data[shop_id]['inventory'][item_type][item_num]['status'] == 'free':
                    courier_name = data.get('courier_name', 'Неизвестный')
                    shops_data[shop_id]['inventory'][item_type][item_num] = {
                        "status": "taken",
                        "courier": courier_name,
                        "taken_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    save_shops(shops_data)
                    emit('inventory_updated', {
                        'shop_id': shop_id,
                        'action': 'give',
                        'item_type': item_type,
                        'item_num': item_num
                    }, broadcast=True)
                    
        elif action == 'take':
            if item_num in shops_data[shop_id]['inventory'][item_type]:
                shops_data[shop_id]['inventory'][item_type][item_num] = {
                    "status": "free",
                    "courier": None,
                    "taken_at": None
                }
                save_shops(shops_data)
                emit('inventory_updated', {
                    'shop_id': shop_id,
                    'action': 'take',
                    'item_type': item_type,
                    'item_num': item_num
                }, broadcast=True)
                
        elif action == 'force_free':
            if item_num in shops_data[shop_id]['inventory'][item_type]:
                shops_data[shop_id]['inventory'][item_type][item_num] = {
                    "status": "free",
                    "courier": None,
                    "taken_at": None
                }
                save_shops(shops_data)
                emit('inventory_updated', {
                    'shop_id': shop_id,
                    'action': 'force_free',
                    'item_type': item_type,
                    'item_num': item_num
                }, broadcast=True)
                
    except Exception as e:
        print(f"Error in inventory_update: {e}")

@socketio.on('inventory_courier_add')
def handle_inventory_courier_add(data):
    try:
        shops_data = load_shops()
        shop_id = str(data.get('shop_id'))
        courier_name = data.get('courier_name')
        
        if shop_id not in shops_data:
            return
        
        # Проверка на дубликат
        for existing in shops_data[shop_id].get('inventory_couriers', {}).values():
            if existing.lower() == courier_name.lower():
                emit('inventory_courier_error', {'error': f'Курьер "{courier_name}" уже существует'}, to=request.sid)
                return
        
        courier_id = str(int(datetime.now().timestamp() * 1000))
        if 'inventory_couriers' not in shops_data[shop_id]:
            shops_data[shop_id]['inventory_couriers'] = {}
        shops_data[shop_id]['inventory_couriers'][courier_id] = courier_name
        save_shops(shops_data)
        
        emit('inventory_courier_added', {
            'shop_id': shop_id,
            'courier_id': courier_id,
            'courier_name': courier_name
        }, broadcast=True)
    except Exception as e:
        print(f"Error in inventory_courier_add: {e}")

@socketio.on('inventory_courier_remove')
def handle_inventory_courier_remove(data):
    try:
        shops_data = load_shops()
        shop_id = str(data.get('shop_id'))
        courier_id = data.get('courier_id')
        
        if shop_id not in shops_data:
            return
        
        courier_name = shops_data[shop_id].get('inventory_couriers', {}).get(courier_id)
        if courier_name:
            # Освобождаем все предметы курьера
            for itype in shops_data[shop_id]['inventory']:
                for num, item in shops_data[shop_id]['inventory'][itype].items():
                    if item.get('courier') == courier_name:
                        shops_data[shop_id]['inventory'][itype][num] = {
                            "status": "free",
                            "courier": None,
                            "taken_at": None
                        }
            if 'inventory_couriers' in shops_data[shop_id]:
                shops_data[shop_id]['inventory_couriers'].pop(courier_id, None)
            save_shops(shops_data)
            
            emit('inventory_courier_removed', {
                'shop_id': shop_id,
                'courier_id': courier_id
            }, broadcast=True)
    except Exception as e:
        print(f"Error in inventory_courier_remove: {e}")

# События для графика работы
@socketio.on('schedule_update')
def handle_schedule_update(data):
    try:
        shops_data = load_shops()
        shop_id = str(data.get('shop_id'))
        region_id = str(data.get('region_id'))
        courier_id = data.get('courier_id')
        date_str = data.get('date')
        new_status = data.get('status')
        
        print(f"📝 schedule_update: shop={shop_id}, region={region_id}, courier={courier_id}, date={date_str}, status={new_status}")
        
        if shop_id in shops_data and region_id in shops_data[shop_id]['schedule']:
            if 'statuses' not in shops_data[shop_id]['schedule'][region_id]:
                shops_data[shop_id]['schedule'][region_id]['statuses'] = {}
            if courier_id not in shops_data[shop_id]['schedule'][region_id]['statuses']:
                shops_data[shop_id]['schedule'][region_id]['statuses'][courier_id] = {}
            
            shops_data[shop_id]['schedule'][region_id]['statuses'][courier_id][date_str] = new_status
            save_shops(shops_data)
            emit('schedule_updated', {
                'shop_id': shop_id,
                'region_id': region_id,
                'courier_id': courier_id,
                'date': date_str,
                'status': new_status
            }, broadcast=True)
            print(f"✅ Статус сохранён")
    except Exception as e:
        print(f"Error in schedule_update: {e}")

@socketio.on('schedule_region_rename')
def handle_schedule_region_rename(data):
    try:
        shops_data = load_shops()
        shop_id = str(data.get('shop_id'))
        region_id = str(data.get('region_id'))
        new_name = data.get('new_name')
        
        if shop_id in shops_data and region_id in shops_data[shop_id]['schedule']:
            shops_data[shop_id]['schedule'][region_id]['name'] = new_name
            save_shops(shops_data)
            emit('region_renamed', {
                'shop_id': shop_id,
                'region_id': region_id,
                'new_name': new_name
            }, broadcast=True)
            print(f"✅ Район переименован: {new_name}")
    except Exception as e:
        print(f"Error in schedule_region_rename: {e}")

@socketio.on('schedule_courier_add')
def handle_schedule_courier_add(data):
    try:
        shops_data = load_shops()
        shop_id = str(data.get('shop_id'))
        region_id = str(data.get('region_id'))
        courier_name = data.get('courier_name')
        
        print(f"📝 Добавление курьера в график: shop={shop_id}, region={region_id}, name={courier_name}")
        
        if shop_id not in shops_data or region_id not in shops_data[shop_id]['schedule']:
            print(f"❌ Точка или район не найдены")
            return
        
        courier_id = str(int(datetime.now().timestamp() * 1000))
        if 'couriers' not in shops_data[shop_id]['schedule'][region_id]:
            shops_data[shop_id]['schedule'][region_id]['couriers'] = {}
        shops_data[shop_id]['schedule'][region_id]['couriers'][courier_id] = courier_name
        save_shops(shops_data)
        
        emit('schedule_courier_added', {
            'shop_id': shop_id,
            'region_id': region_id,
            'courier_id': courier_id,
            'courier_name': courier_name
        }, broadcast=True)
        print(f"✅ Курьер добавлен, ID={courier_id}")
    except Exception as e:
        print(f"Error in schedule_courier_add: {e}")

@socketio.on('schedule_courier_remove')
def handle_schedule_courier_remove(data):
    try:
        shops_data = load_shops()
        shop_id = str(data.get('shop_id'))
        region_id = str(data.get('region_id'))
        courier_id = data.get('courier_id')
        
        if shop_id in shops_data and region_id in shops_data[shop_id]['schedule']:
            if 'couriers' in shops_data[shop_id]['schedule'][region_id]:
                shops_data[shop_id]['schedule'][region_id]['couriers'].pop(courier_id, None)
            if 'statuses' in shops_data[shop_id]['schedule'][region_id]:
                shops_data[shop_id]['schedule'][region_id]['statuses'].pop(courier_id, None)
            save_shops(shops_data)
            
            emit('schedule_courier_removed', {
                'shop_id': shop_id,
                'region_id': region_id,
                'courier_id': courier_id
            }, broadcast=True)
            print(f"✅ Курьер удалён из района")
    except Exception as e:
        print(f"Error in schedule_courier_remove: {e}")

@socketio.on('shop_rename')
def handle_shop_rename(data):
    try:
        shops_data = load_shops()
        shop_id = str(data.get('shop_id'))
        new_name = data.get('new_name')
        
        if shop_id in shops_data:
            shops_data[shop_id]['name'] = new_name
            save_shops(shops_data)
            emit('shop_renamed', {
                'shop_id': shop_id,
                'new_name': new_name
            }, broadcast=True)
            print(f"✅ Точка переименована: {new_name}")
    except Exception as e:
        print(f"Error in shop_rename: {e}")

# ============ HTTP API ============
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/shops', methods=['GET'])
def get_shops():
    shops = load_shops()
    result = {}
    for shop_id, shop in shops.items():
        result[shop_id] = {
            "id": shop["id"],
            "name": shop["name"]
        }
    return jsonify(result)

@app.route('/api/shops/<shop_id>', methods=['GET'])
def get_shop(shop_id):
    shops = load_shops()
    if shop_id in shops:
        return jsonify(shops[shop_id])
    return jsonify({"error": "Точка не найдена"}), 404

@app.route('/api/shops/<shop_id>/inventory/couriers', methods=['GET'])
def get_shop_couriers(shop_id):
    shops = load_shops()
    if shop_id in shops:
        return jsonify(shops[shop_id].get('inventory_couriers', {}))
    return jsonify({})

@app.route('/api/shops/<shop_id>/inventory/items/free/<item_type>', methods=['GET'])
def get_shop_free_items(shop_id, item_type):
    shops = load_shops()
    if shop_id in shops and item_type in shops[shop_id]['inventory']:
        free_items = []
        for num, item in shops[shop_id]['inventory'][item_type].items():
            if item['status'] == 'free':
                free_items.append(num)
        return jsonify(sorted(free_items, key=int))
    return jsonify([])

@app.route('/api/shops/<shop_id>/inventory/items/taken', methods=['GET'])
def get_shop_taken_items(shop_id):
    shops = load_shops()
    if shop_id not in shops:
        return jsonify([])
    
    items = []
    item_types = ["bags", "batteries", "bicycles", "raincoats", "tools"]
    type_display = {
        "bags": "🎒 Сумка",
        "batteries": "🔋 Аккумулятор",
        "bicycles": "🚲 Велосипед",
        "raincoats": "🌧️ Дождевик",
        "tools": "🛠️ Инструмент"
    }
    tool_names = {
        "1": "Насос", "2": "Молоток", "3": "Ключ",
        "4": "Отвертка", "5": "Плоскогубцы", "6": "Шуруповерт"
    }
    
    for item_type in item_types:
        for num, item in shops[shop_id]['inventory'][item_type].items():
            if item['status'] == 'taken' and item['courier']:
                taken_at = item['taken_at']
                if taken_at:
                    try:
                        taken_dt = datetime.fromisoformat(taken_at)
                        hours_ago = (datetime.now() - taken_dt).total_seconds() / 3600
                        time_str = f"{hours_ago:.1f} ч назад"
                    except:
                        time_str = taken_at
                else:
                    time_str = "время не указано"
                
                items.append({
                    "type": item_type,
                    "type_display": type_display[item_type],
                    "number": num,
                    "courier": item['courier'],
                    "taken_at": taken_at,
                    "time_ago": time_str,
                    "tool_name": tool_names.get(num) if item_type == "tools" else None
                })
    return jsonify(items)

@app.route('/api/shops/<shop_id>/inventory/stats', methods=['GET'])
def get_shop_inventory_stats(shop_id):
    shops = load_shops()
    if shop_id not in shops:
        return jsonify({})
    
    stats = {}
    item_types = ["bags", "batteries", "bicycles", "raincoats", "tools"]
    totals = {"bags": 20, "batteries": 20, "bicycles": 10, "raincoats": 15, "tools": 6}
    
    for item_type in item_types:
        total = totals[item_type]
        taken = sum(1 for item in shops[shop_id]['inventory'][item_type].values() if item['status'] == 'taken')
        free = total - taken
        percent = int((taken / total) * 100) if total > 0 else 0
        stats[item_type] = {
            "total": total,
            "taken": taken,
            "free": free,
            "percent": percent
        }
    return jsonify(stats)

@app.route('/api/shops/<shop_id>/schedule', methods=['GET'])
def get_shop_schedule(shop_id):
    shops = load_shops()
    if shop_id in shops:
        return jsonify(shops[shop_id]['schedule'])
    return jsonify({})

# НОВЫЙ API ДЛЯ СОХРАНЕНИЯ ГРАФИКА
@app.route('/api/shops/<shop_id>/schedule', methods=['POST'])
def save_shop_schedule(shop_id):
    try:
        shops = load_shops()
        if shop_id not in shops:
            return jsonify({"success": False, "error": "Точка не найдена"}), 404
        
        schedule_data = request.get_json()
        shops[shop_id]['schedule'] = schedule_data
        save_shops(shops)
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error saving schedule: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    local_ip = get_local_ip()
    print("=" * 60)
    print("🚀 СИСТЕМА УЧЁТА ИНВЕНТАРЯ - ТОРГОВЫЕ ТОЧКИ")
    print("=" * 60)
    print(f"🌐 Локальный доступ: http://127.0.0.1:5000")
    print(f"🌐 Доступ с других ПК: http://{local_ip}:5000")
    print("=" * 60)
    print("🏪 7 ТОРГОВЫХ ТОЧЕК:")
    print("   1. Центральная    5. Западная")
    print("   2. Северная       6. Привокзальная")
    print("   3. Южная          7. ТРЦ")
    print("   4. Восточная")
    print("=" * 60)
    print("📋 В КАЖДОЙ ТОЧКЕ:")
    print("   • 7 районов для графика работы")
    print("   • Управление курьерами в каждом районе")
    print("   • Управление инвентарём")
    print("   • Синхронизация между пользователями")
    print("=" * 60)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
