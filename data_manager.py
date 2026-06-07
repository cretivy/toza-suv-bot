import json
import os
import uuid
from datetime import datetime

STATE_FILE = "state.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"active_driver_id": None, "customers": [], "orders": []}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure required keys exist
            if "orders" not in data: data["orders"] = []
            if "customers" not in data: data["customers"] = []
            if "active_driver_id" not in data: data["active_driver_id"] = None
            return data
    except (json.JSONDecodeError, ValueError):
        return {"active_driver_id": None, "customers": [], "orders": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def get_active_driver_id():
    return load_state().get("active_driver_id")

def set_active_driver_id(driver_id):
    state = load_state()
    state["active_driver_id"] = driver_id
    save_state(state)

def add_customer(customer_id):
    state = load_state()
    if customer_id not in state["customers"]:
        state["customers"].append(customer_id)
        save_state(state)

def get_customers_count():
    return len(load_state().get("customers", []))

def add_order(order_data):
    state = load_state()
    if "orders" not in state:
        state["orders"] = []
    
    # Add timestamp if not present
    if "timestamp" not in order_data:
        order_data["timestamp"] = datetime.now().isoformat()
    
    if "id" not in order_data:
        order_data["id"] = str(uuid.uuid4())[:8]
    
    if "status" not in order_data:
        order_data["status"] = "Pending"
    
    state["orders"].append(order_data)
    save_state(state)

def get_orders():
    return load_state().get("orders", [])

def get_average_interval(customer_id):
    orders = [o for o in get_orders() if o['customer_id'] == customer_id]
    if len(orders) < 2:
        return 7  # Default to 7 days if not enough data
    
    dates = [datetime.fromisoformat(o['timestamp']) for o in orders]
    dates.sort()
    
    diffs = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
    avg = sum(diffs) / len(diffs)
    return max(1, round(avg))

def get_last_order_date(customer_id):
    orders = [o for o in get_orders() if o['customer_id'] == customer_id]
    if not orders:
        return None
    dates = [datetime.fromisoformat(o['timestamp']) for o in orders]
    return max(dates)

def update_order_status(order_id, status):
    state = load_state()
    for order in state.get("orders", []):
        if order.get("id") == order_id:
            order["status"] = status
            if status == "Delivered":
                order["delivered_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_state(state)
            return True
    return False

def mark_order_delivered(order_id):
    return update_order_status(order_id, "Delivered")

def get_state():
    return load_state()
