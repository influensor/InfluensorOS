import os
import json

CUSTOMERS_DIR = "customers"

def load_all_customers():
    customers = []

    if not os.path.exists(CUSTOMERS_DIR):
        print("[customer_loader] customers directory not found")
        return customers

    for fname in os.listdir(CUSTOMERS_DIR):
        if not fname.endswith(".json"):
            continue

        path = os.path.join(CUSTOMERS_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                customers.append(data)
        except Exception as e:
            print(f"[customer_loader] error loading {fname}: {e}")

    return customers
