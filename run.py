import http.server
import socketserver
import json
import urllib.parse
import webbrowser
import threading
import sys
import time
from datetime import datetime

PORT = 8000

# Mock Database & State Engine matching Odoo StockSense Models
DB = {
    "categories": [
        {"id": 1, "name": "Raw Materials", "description": "Raw materials and components"},
        {"id": 2, "name": "Office Equipment", "description": "Office furniture and supplies"},
        {"id": 3, "name": "Electronics", "description": "Electronic devices and components"},
        {"id": 4, "name": "Safety Equipment", "description": "Safety gear and protective equipment"}
    ],
    "warehouses": [
        {"id": 1, "name": "Main Warehouse", "code": "WH-01", "location": "WH-01/Stock"},
        {"id": 2, "name": "Production Floor", "code": "WH-02", "location": "WH-02/Stock"},
        {"id": 3, "name": "Secondary Warehouse", "code": "WH-03", "location": "WH-03/Stock"}
    ],
    "products": [
        {"id": 1, "name": "Steel Rods", "sku": "SR-001", "category_id": 1, "price": 250.0, "qty_available": 100.0, "reorder_point": 50.0, "reorder_qty": 100.0, "uom": "kg"},
        {"id": 2, "name": "Office Chairs", "sku": "OC-002", "category_id": 2, "price": 350.0, "qty_available": 4.0, "reorder_point": 10.0, "reorder_qty": 20.0, "uom": "Units"},
        {"id": 3, "name": "Laptops", "sku": "LT-003", "category_id": 3, "price": 1200.0, "qty_available": 0.0, "reorder_point": 5.0, "reorder_qty": 15.0, "uom": "Units"},
        {"id": 4, "name": "Printer Paper (500 sheets)", "sku": "PP-004", "category_id": 2, "price": 4.5, "qty_available": 45.0, "reorder_point": 20.0, "reorder_qty": 50.0, "uom": "Packs"},
        {"id": 5, "name": "Safety Helmets", "sku": "SH-005", "category_id": 4, "price": 65.0, "qty_available": 18.0, "reorder_point": 15.0, "reorder_qty": 30.0, "uom": "Units"},
        {"id": 6, "name": "Electrical Cables (100m)", "sku": "EC-006", "category_id": 1, "price": 80.0, "qty_available": 2.0, "reorder_point": 10.0, "reorder_qty": 25.0, "uom": "Rolls"}
    ],
    "suppliers": [
        {"id": 1, "name": "ABC Corporation", "email": "supplier@abccorp.com", "phone": "+1-555-0100"}
    ],
    "customers": [
        {"id": 1, "name": "XYZ Limited", "email": "customer@xyzltd.com", "phone": "+1-555-0200"}
    ],
    "receipts": [
        {
            "id": 1, 
            "name": "RCP/00001", 
            "supplier_id": 1, 
            "warehouse_id": 1, 
            "date": "2026-09-25 10:00:00", 
            "state": "done",
            "notes": "Initial stock receipt",
            "lines": [
                {"product_id": 1, "quantity": 100.0},
                {"product_id": 4, "quantity": 45.0}
            ]
        }
    ],
    "deliveries": [
        {
            "id": 1, 
            "name": "DLV/00001", 
            "customer_id": 1, 
            "warehouse_id": 1, 
            "date": "2026-09-26 09:30:00", 
            "state": "ready",
            "notes": "Urgent shipment for project Alpha",
            "lines": [
                {"product_id": 5, "quantity": 2.0}
            ]
        }
    ],
    "transfers": [],
    "adjustments": [],
    "ledger": [
        {
            "id": 1,
            "date": "2026-09-25 10:00:00",
            "product_id": 1,
            "product_name": "Steel Rods",
            "sku": "SR-001",
            "type": "receipt",
            "source": "Vendors",
            "destination": "WH-01/Stock",
            "qty": 100.0,
            "ref": "RCP/00001",
            "user": "Administrator"
        },
        {
            "id": 2,
            "date": "2026-09-25 10:05:00",
            "product_id": 4,
            "product_name": "Printer Paper (500 sheets)",
            "sku": "PP-004",
            "type": "receipt",
            "source": "Vendors",
            "destination": "WH-01/Stock",
            "qty": 45.0,
            "ref": "RCP/00001",
            "user": "Administrator"
        }
    ]
}

def get_product_status(qty):
    if qty > 5:
        return {"status": "available", "label": "Available", "badge": "badge-success"}
    elif qty > 0:
        return {"status": "low", "label": "Low Stock", "badge": "badge-warning"}
    else:
        return {"status": "unavailable", "label": "Out of Stock", "badge": "badge-danger"}

class StockSenseHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Suppress detailed request logs for cleaner console output

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == "/api/data":
            # Calculate dynamic KPIs
            total_products = len(DB["products"])
            low_stock = sum(1 for p in DB["products"] if 0 < p["qty_available"] <= 5)
            out_of_stock = sum(1 for p in DB["products"] if p["qty_available"] == 0)
            pending_receipts = sum(1 for r in DB["receipts"] if r["state"] in ["draft", "confirmed"])
            pending_deliveries = sum(1 for d in DB["deliveries"] if d["state"] in ["draft", "ready", "in_transit"])
            scheduled_transfers = sum(1 for t in DB["transfers"] if t["state"] in ["draft", "confirmed"])

            # Enrich products with categories and status
            enriched_products = []
            cat_map = {c["id"]: c["name"] for c in DB["categories"]}
            for p in DB["products"]:
                p_copy = dict(p)
                p_copy["category_name"] = cat_map.get(p["category_id"], "Uncategorized")
                p_copy["status_info"] = get_product_status(p["qty_available"])
                enriched_products.append(p_copy)

            response = {
                "kpis": {
                    "total_products": total_products,
                    "low_stock": low_stock,
                    "out_of_stock": out_of_stock,
                    "pending_receipts": pending_receipts,
                    "pending_deliveries": pending_deliveries,
                    "scheduled_transfers": scheduled_transfers
                },
                "products": enriched_products,
                "categories": DB["categories"],
                "warehouses": DB["warehouses"],
                "suppliers": DB["suppliers"],
                "customers": DB["customers"],
                "receipts": DB["receipts"],
                "deliveries": DB["deliveries"],
                "transfers": DB["transfers"],
                "adjustments": DB["adjustments"],
                "ledger": sorted(DB["ledger"], key=lambda x: x["id"], reverse=True)
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        # Serve static files (index.html, style.css, script.js) directly from filesystem
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        data = json.loads(body) if body else {}

        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == "/api/receipt/create":
            new_id = len(DB["receipts"]) + 1
            rec_num = f"RCP/{new_id:05d}"
            receipt = {
                "id": new_id,
                "name": rec_num,
                "supplier_id": int(data.get("supplier_id", 1)),
                "warehouse_id": int(data.get("warehouse_id", 1)),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "state": "done",
                "notes": data.get("notes", "Receipt created via StockSense UI"),
                "lines": data.get("lines", [])
            }
            DB["receipts"].append(receipt)

            # Update product stock & create ledger entries
            prod_map = {p["id"]: p for p in DB["products"]}
            for line in receipt["lines"]:
                pid = int(line["product_id"])
                qty = float(line["quantity"])
                if pid in prod_map:
                    prod_map[pid]["qty_available"] += qty
                    DB["ledger"].append({
                        "id": len(DB["ledger"]) + 1,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "product_id": pid,
                        "product_name": prod_map[pid]["name"],
                        "sku": prod_map[pid]["sku"],
                        "type": "receipt",
                        "source": "Vendors",
                        "destination": "WH-01/Stock",
                        "qty": qty,
                        "ref": rec_num,
                        "user": "Inventory Manager"
                    })

            self.send_json_response({"success": True, "message": f"Receipt {rec_num} created and stock updated successfully!"})

        elif path == "/api/delivery/create":
            new_id = len(DB["deliveries"]) + 1
            dlv_num = f"DLV/{new_id:05d}"

            # Stock check validation
            prod_map = {p["id"]: p for p in DB["products"]}
            for line in data.get("lines", []):
                pid = int(line["product_id"])
                qty = float(line["quantity"])
                if pid in prod_map and prod_map[pid]["qty_available"] < qty:
                    self.send_json_response({"success": False, "message": f"Insufficient stock for {prod_map[pid]['name']}. Available: {prod_map[pid]['qty_available']}"}, status=400)
                    return

            delivery = {
                "id": new_id,
                "name": dlv_num,
                "customer_id": int(data.get("customer_id", 1)),
                "warehouse_id": int(data.get("warehouse_id", 1)),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "state": "done",
                "notes": data.get("notes", "Delivery order executed"),
                "lines": data.get("lines", [])
            }
            DB["deliveries"].append(delivery)

            # Deduct stock & log ledger
            for line in delivery["lines"]:
                pid = int(line["product_id"])
                qty = float(line["quantity"])
                if pid in prod_map:
                    prod_map[pid]["qty_available"] -= qty
                    DB["ledger"].append({
                        "id": len(DB["ledger"]) + 1,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "product_id": pid,
                        "product_name": prod_map[pid]["name"],
                        "sku": prod_map[pid]["sku"],
                        "type": "delivery",
                        "source": "WH-01/Stock",
                        "destination": "Customers",
                        "qty": qty,
                        "ref": dlv_num,
                        "user": "Inventory Manager"
                    })

            self.send_json_response({"success": True, "message": f"Delivery Order {dlv_num} completed and stock updated!"})

        elif path == "/api/transfer/create":
            new_id = len(DB["transfers"]) + 1
            trf_num = f"TRF/{new_id:05d}"
            prod_map = {p["id"]: p for p in DB["products"]}

            transfer = {
                "id": new_id,
                "name": trf_num,
                "src_wh": data.get("src_wh", "Main Warehouse"),
                "dest_wh": data.get("dest_wh", "Production Floor"),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "state": "done",
                "lines": data.get("lines", [])
            }
            DB["transfers"].append(transfer)

            for line in transfer["lines"]:
                pid = int(line["product_id"])
                qty = float(line["quantity"])
                if pid in prod_map:
                    DB["ledger"].append({
                        "id": len(DB["ledger"]) + 1,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "product_id": pid,
                        "product_name": prod_map[pid]["name"],
                        "sku": prod_map[pid]["sku"],
                        "type": "transfer",
                        "source": transfer["src_wh"],
                        "destination": transfer["dest_wh"],
                        "qty": qty,
                        "ref": trf_num,
                        "user": "Warehouse Staff"
                    })

            self.send_json_response({"success": True, "message": f"Internal Transfer {trf_num} processed!"})

        elif path == "/api/adjustment/create":
            new_id = len(DB["adjustments"]) + 1
            adj_num = f"ADJ/{new_id:05d}"
            pid = int(data.get("product_id"))
            physical_qty = float(data.get("physical_qty"))
            reason = data.get("reason", "Physical Count Variance")

            prod = next((p for p in DB["products"] if p["id"] == pid), None)
            if prod:
                diff = physical_qty - prod["qty_available"]
                old_qty = prod["qty_available"]
                prod["qty_available"] = physical_qty

                DB["adjustments"].append({
                    "id": new_id,
                    "name": adj_num,
                    "product_id": pid,
                    "product_name": prod["name"],
                    "old_qty": old_qty,
                    "new_qty": physical_qty,
                    "diff": diff,
                    "reason": reason,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "state": "done"
                })

                DB["ledger"].append({
                    "id": len(DB["ledger"]) + 1,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "product_id": pid,
                    "product_name": prod["name"],
                    "sku": prod["sku"],
                    "type": "adjustment",
                    "source": "Physical Audit",
                    "destination": "WH-01/Stock",
                    "qty": abs(diff),
                    "ref": adj_num,
                    "user": "Inventory Manager"
                })

                self.send_json_response({"success": True, "message": f"Stock Adjustment {adj_num} applied! Stock updated to {physical_qty}."})
            else:
                self.send_json_response({"success": False, "message": "Product not found."}, status=400)

        elif path == "/api/product/create":
            new_id = len(DB["products"]) + 1
            product = {
                "id": new_id,
                "name": data.get("name"),
                "sku": data.get("sku"),
                "category_id": int(data.get("category_id", 1)),
                "price": float(data.get("price", 0.0)),
                "qty_available": float(data.get("qty_available", 0.0)),
                "reorder_point": float(data.get("reorder_point", 5.0)),
                "reorder_qty": float(data.get("reorder_qty", 10.0)),
                "uom": data.get("uom", "Units")
            }
            DB["products"].append(product)
            self.send_json_response({"success": True, "message": f"Product '{product['name']}' created successfully!"})
        else:
            self.send_json_response({"success": False, "message": "Unknown endpoint"}, status=404)

    def send_json_response(self, obj, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockSense - Enterprise Inventory Management System</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --accent: #06b6d4;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --glass-bg: rgba(30, 41, 59, 0.7);
            --glass-border: rgba(255, 255, 255, 0.08);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        }

        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* Sidebar */
        .sidebar {
            width: 260px;
            background: rgba(15, 23, 42, 0.95);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 1.5rem 1rem;
            backdrop-filter: blur(12px);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0 0.5rem 1.5rem 0.5rem;
            border-bottom: 1px solid var(--border);
            margin-bottom: 1.5rem;
        }

        .brand-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
        }

        .brand-text h1 {
            font-size: 1.25rem;
            font-weight: 800;
            background: linear-gradient(90deg, #fff, var(--text-muted));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-text span {
            font-size: 0.7rem;
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }

        .nav-menu {
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
            flex: 1;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 0.85rem;
            padding: 0.75rem 1rem;
            border-radius: 10px;
            color: var(--text-muted);
            text-decoration: none;
            font-weight: 500;
            font-size: 0.92rem;
            transition: all 0.25s ease;
            cursor: pointer;
        }

        .nav-item:hover, .nav-item.active {
            background: linear-gradient(90deg, rgba(99, 102, 241, 0.15), rgba(6, 182, 212, 0.05));
            color: #fff;
            border-left: 3px solid var(--primary);
        }

        .nav-item i {
            font-size: 1.1rem;
            width: 20px;
        }

        .user-profile {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-top: auto;
        }

        .avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
        }

        .user-info h4 {
            font-size: 0.85rem;
            font-weight: 600;
        }

        .user-info p {
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        /* Main Content */
        .main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
            background: radial-gradient(circle at top right, rgba(99, 102, 241, 0.08), transparent 40%);
        }

        header {
            padding: 1.25rem 2rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--glass-bg);
            backdrop-filter: blur(8px);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-title h2 {
            font-size: 1.4rem;
            font-weight: 700;
        }

        .header-title p {
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .action-btns {
            display: flex;
            gap: 0.75rem;
        }

        .btn {
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.85rem;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.2s ease;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            color: #fff;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
        }

        .btn-secondary {
            background: var(--bg-card);
            color: var(--text-main);
            border: 1px solid var(--border);
        }

        .btn-secondary:hover {
            background: var(--bg-card-hover);
        }

        .content {
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }

        /* KPI Cards Grid */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.25rem;
        }

        .kpi-card {
            background: var(--bg-card);
            border: 1px solid var(--glass-border);
            padding: 1.25rem;
            border-radius: 14px;
            display: flex;
            align-items: center;
            gap: 1rem;
            position: relative;
            overflow: hidden;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }

        .kpi-card:hover {
            transform: translateY(-3px);
            border-color: var(--primary);
        }

        .kpi-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
        }

        .kpi-blue { background: rgba(99, 102, 241, 0.15); color: var(--primary); }
        .kpi-yellow { background: rgba(245, 158, 11, 0.15); color: var(--warning); }
        .kpi-red { background: rgba(239, 68, 68, 0.15); color: var(--danger); }
        .kpi-green { background: rgba(16, 185, 129, 0.15); color: var(--success); }
        .kpi-cyan { background: rgba(6, 182, 212, 0.15); color: var(--accent); }

        .kpi-data h3 {
            font-size: 1.5rem;
            font-weight: 800;
        }

        .kpi-data p {
            font-size: 0.8rem;
            color: var(--text-muted);
            font-weight: 500;
        }

        /* Tables & Panels */
        .panel {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .panel-header h3 {
            font-size: 1.1rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .search-bar {
            position: relative;
            width: 250px;
        }

        .search-bar input {
            width: 100%;
            padding: 0.5rem 0.8rem 0.5rem 2.2rem;
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: #fff;
            font-size: 0.85rem;
        }

        .search-bar i {
            position: absolute;
            left: 0.8rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 0.8rem;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.88rem;
        }

        th {
            padding: 0.8rem 1rem;
            color: var(--text-muted);
            font-weight: 600;
            border-bottom: 1px solid var(--border);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
        }

        td {
            padding: 0.9rem 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            color: var(--text-main);
        }

        tr:hover td {
            background: rgba(255, 255, 255, 0.02);
        }

        /* Badges */
        .badge {
            padding: 0.25rem 0.6rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
        }

        .badge-success { background: rgba(16, 185, 129, 0.2); color: #34d399; }
        .badge-warning { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
        .badge-danger { background: rgba(239, 68, 68, 0.2); color: #f87171; }
        .badge-primary { background: rgba(99, 102, 241, 0.2); color: #818cf8; }

        /* Modal */
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(5px);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }

        .modal-overlay.active { display: flex; }

        .modal {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            width: 480px;
            max-width: 90%;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-header h3 { font-size: 1.15rem; font-weight: 700; }
        .close-modal { cursor: pointer; color: var(--text-muted); font-size: 1.2rem; }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }

        .form-group label {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
        }

        .form-group input, .form-group select, .form-group textarea {
            padding: 0.65rem 0.8rem;
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: #fff;
            font-size: 0.88rem;
        }

        .form-group input:focus, .form-group select:focus {
            border-color: var(--primary);
            outline: none;
        }

        /* Toast notification */
        .toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            padding: 0.9rem 1.4rem;
            border-radius: 10px;
            background: var(--bg-card);
            border: 1px solid var(--primary);
            color: #fff;
            font-size: 0.88rem;
            font-weight: 600;
            box-shadow: 0 10px 25px rgba(0,0,0,0.4);
            display: none;
            align-items: center;
            gap: 0.6rem;
            z-index: 2000;
        }
    </style>
</head>
<body>

    <!-- Sidebar -->
    <div class="sidebar">
        <div class="brand">
            <div class="brand-icon"><i class="fa-solid fa-boxes-stacked"></i></div>
            <div class="brand-text">
                <h1>StockSense</h1>
                <span>Enterprise IMS</span>
            </div>
        </div>
        <div class="nav-menu">
            <div class="nav-item active" onclick="switchTab('dashboard')"><i class="fa-solid fa-chart-pie"></i> Dashboard</div>
            <div class="nav-item" onclick="switchTab('products')"><i class="fa-solid fa-box"></i> Products & Stock</div>
            <div class="nav-item" onclick="switchTab('receipts')"><i class="fa-solid fa-truck-ramp-box"></i> Goods Receipts</div>
            <div class="nav-item" onclick="switchTab('deliveries')"><i class="fa-solid fa-truck-fast"></i> Delivery Orders</div>
            <div class="nav-item" onclick="switchTab('transfers')"><i class="fa-solid fa-arrow-right-arrow-left"></i> Internal Transfers</div>
            <div class="nav-item" onclick="switchTab('adjustments')"><i class="fa-solid fa-sliders"></i> Stock Adjustments</div>
            <div class="nav-item" onclick="switchTab('ledger')"><i class="fa-solid fa-receipt"></i> Stock Ledger</div>
        </div>
        <div class="user-profile">
            <div class="avatar">IM</div>
            <div class="user-info">
                <h4>Inventory Manager</h4>
                <p>Odoo StockSense Admin</p>
            </div>
        </div>
    </div>

    <!-- Main Container -->
    <div class="main-container">
        <header>
            <div class="header-title">
                <h2 id="page-title">Inventory Dashboard</h2>
                <p id="page-subtitle">Real-time stock operations and KPI overview</p>
            </div>
            <div class="action-btns">
                <button class="btn btn-secondary" onclick="fetchData()"><i class="fa-solid fa-rotate"></i> Refresh</button>
                <button class="btn btn-primary" onclick="openModal('receipt')"><i class="fa-solid fa-plus"></i> New Receipt</button>
                <button class="btn btn-primary" style="background: linear-gradient(135deg, var(--accent), #0284c7);" onclick="openModal('delivery')"><i class="fa-solid fa-paper-plane"></i> New Delivery</button>
            </div>
        </header>

        <div class="content">

            <!-- KPIs -->
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-icon kpi-blue"><i class="fa-solid fa-cubes"></i></div>
                    <div class="kpi-data">
                        <h3 id="kpi-products">0</h3>
                        <p>Total Products</p>
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon kpi-yellow"><i class="fa-solid fa-triangle-exclamation"></i></div>
                    <div class="kpi-data">
                        <h3 id="kpi-low">0</h3>
                        <p>Low Stock Items</p>
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon kpi-red"><i class="fa-solid fa-circle-xmark"></i></div>
                    <div class="kpi-data">
                        <h3 id="kpi-out">0</h3>
                        <p>Out of Stock</p>
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon kpi-green"><i class="fa-solid fa-truck-arrow-right"></i></div>
                    <div class="kpi-data">
                        <h3 id="kpi-receipts">0</h3>
                        <p>Completed Receipts</p>
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon kpi-cyan"><i class="fa-solid fa-truck-moving"></i></div>
                    <div class="kpi-data">
                        <h3 id="kpi-deliveries">0</h3>
                        <p>Completed Deliveries</p>
                    </div>
                </div>
            </div>

            <!-- Dynamic Section Content -->
            <div id="tab-content" class="panel">
                <!-- Injected via JS -->
            </div>

        </div>
    </div>

    <!-- Universal Action Modal -->
    <div class="modal-overlay" id="modal-overlay">
        <div class="modal">
            <div class="modal-header">
                <h3 id="modal-title">Action Form</h3>
                <span class="close-modal" onclick="closeModal()">&times;</span>
            </div>
            <div id="modal-body">
                <!-- Dynamic Form -->
            </div>
        </div>
    </div>

    <!-- Toast Notification -->
    <div class="toast" id="toast">
        <i class="fa-solid fa-circle-check" style="color: var(--success);"></i>
        <span id="toast-msg">Operation completed!</span>
    </div>

    <script>
        let currentTab = 'dashboard';
        let appData = null;

        async function fetchData() {
            try {
                const res = await fetch('/api/data');
                appData = await res.json();
                renderKPIs();
                renderTab();
            } catch (err) {
                showToast("Error connecting to StockSense backend", true);
            }
        }

        function renderKPIs() {
            if (!appData) return;
            const k = appData.kpis;
            document.getElementById('kpi-products').innerText = k.total_products;
            document.getElementById('kpi-low').innerText = k.low_stock;
            document.getElementById('kpi-out').innerText = k.out_of_stock;
            document.getElementById('kpi-receipts').innerText = appData.receipts.length;
            document.getElementById('kpi-deliveries').innerText = appData.deliveries.length;
        }

        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            event.currentTarget.classList.add('active');
            
            const titles = {
                'dashboard': ['Inventory Dashboard', 'Real-time stock operations and KPI overview'],
                'products': ['Product Management', 'Master catalog with SKU, reorder points, and location stock'],
                'receipts': ['Goods Receipts', 'Incoming stock records from suppliers'],
                'deliveries': ['Delivery Orders', 'Outgoing customer dispatch workflows'],
                'transfers': ['Internal Transfers', 'Inter-warehouse and location movement control'],
                'adjustments': ['Stock Adjustments', 'Physical count reconciliation and variance log'],
                'ledger': ['Stock Movement Ledger', 'Complete audit trail of all inventory events']
            };

            document.getElementById('page-title').innerText = titles[tab][0];
            document.getElementById('page-subtitle').innerText = titles[tab][1];
            renderTab();
        }

        function renderTab() {
            const container = document.getElementById('tab-content');
            if (!appData) { container.innerHTML = "<p>Loading data...</p>"; return; }

            if (currentTab === 'dashboard' || currentTab === 'products') {
                let html = `
                    <div class="panel-header">
                        <h3><i class="fa-solid fa-boxes-stacked"></i> Products Inventory</h3>
                        <div style="display:flex; gap:0.5rem;">
                            <button class="btn btn-secondary" onclick="openModal('product')"><i class="fa-solid fa-plus"></i> Add Product</button>
                            <div class="search-bar">
                                <i class="fa-solid fa-magnifying-glass"></i>
                                <input type="text" placeholder="Search SKU or Name..." onkeyup="filterProducts(this.value)">
                            </div>
                        </div>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>SKU</th>
                                <th>Product Name</th>
                                <th>Category</th>
                                <th>Price</th>
                                <th>Stock Qty</th>
                                <th>Reorder Point</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="product-rows">
                `;
                appData.products.forEach(p => {
                    html += `
                        <tr>
                            <td><strong style="color:var(--accent);">${p.sku}</strong></td>
                            <td><strong>${p.name}</strong></td>
                            <td>${p.category_name}</td>
                            <td>$${p.price.toFixed(2)}</td>
                            <td><strong style="font-size:1rem;">${p.qty_available} ${p.uom}</strong></td>
                            <td>${p.reorder_point} ${p.uom}</td>
                            <td><span class="badge ${p.status_info.badge}">${p.status_info.label}</span></td>
                            <td>
                                <button class="btn btn-secondary" style="padding:0.3rem 0.6rem; font-size:0.75rem;" onclick="openModal('adjustment', ${p.id})"><i class="fa-solid fa-sliders"></i> Adjust</button>
                            </td>
                        </tr>
                    `;
                });
                html += `</tbody></table>`;
                container.innerHTML = html;
            } else if (currentTab === 'receipts') {
                let html = `
                    <div class="panel-header">
                        <h3><i class="fa-solid fa-truck-ramp-box"></i> Goods Receipts (Incoming)</h3>
                        <button class="btn btn-primary" onclick="openModal('receipt')"><i class="fa-solid fa-plus"></i> New Receipt</button>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Receipt Ref</th>
                                <th>Date</th>
                                <th>Supplier</th>
                                <th>State</th>
                                <th>Items</th>
                                <th>Notes</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                appData.receipts.forEach(r => {
                    const sup = appData.suppliers.find(s => s.id === r.supplier_id)?.name || 'Supplier';
                    html += `
                        <tr>
                            <td><strong style="color:var(--primary);">${r.name}</strong></td>
                            <td>${r.date}</td>
                            <td>${sup}</td>
                            <td><span class="badge badge-success">${r.state.toUpperCase()}</span></td>
                            <td>${r.lines.length} Line(s)</td>
                            <td>${r.notes}</td>
                        </tr>
                    `;
                });
                html += `</tbody></table>`;
                container.innerHTML = html;
            } else if (currentTab === 'deliveries') {
                let html = `
                    <div class="panel-header">
                        <h3><i class="fa-solid fa-truck-fast"></i> Delivery Orders (Outgoing)</h3>
                        <button class="btn btn-primary" style="background: linear-gradient(135deg, var(--accent), #0284c7);" onclick="openModal('delivery')"><i class="fa-solid fa-paper-plane"></i> New Delivery</button>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Delivery Ref</th>
                                <th>Date</th>
                                <th>Customer</th>
                                <th>State</th>
                                <th>Items</th>
                                <th>Notes</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                appData.deliveries.forEach(d => {
                    const cust = appData.customers.find(c => c.id === d.customer_id)?.name || 'Customer';
                    html += `
                        <tr>
                            <td><strong style="color:var(--accent);">${d.name}</strong></td>
                            <td>${d.date}</td>
                            <td>${cust}</td>
                            <td><span class="badge badge-primary">${d.state.toUpperCase()}</span></td>
                            <td>${d.lines.length} Line(s)</td>
                            <td>${d.notes}</td>
                        </tr>
                    `;
                });
                html += `</tbody></table>`;
                container.innerHTML = html;
            } else if (currentTab === 'transfers') {
                let html = `
                    <div class="panel-header">
                        <h3><i class="fa-solid fa-arrow-right-arrow-left"></i> Internal Transfers</h3>
                        <button class="btn btn-secondary" onclick="openModal('transfer')"><i class="fa-solid fa-plus"></i> New Transfer</button>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Transfer Ref</th>
                                <th>Date</th>
                                <th>Source WH</th>
                                <th>Destination WH</th>
                                <th>State</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                appData.transfers.forEach(t => {
                    html += `
                        <tr>
                            <td><strong>${t.name}</strong></td>
                            <td>${t.date}</td>
                            <td>${t.src_wh}</td>
                            <td>${t.dest_wh}</td>
                            <td><span class="badge badge-success">${t.state.toUpperCase()}</span></td>
                        </tr>
                    `;
                });
                if (appData.transfers.length === 0) {
                    html += `<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">No internal transfers logged yet. Click 'New Transfer' to test.</td></tr>`;
                }
                html += `</tbody></table>`;
                container.innerHTML = html;
            } else if (currentTab === 'adjustments') {
                let html = `
                    <div class="panel-header">
                        <h3><i class="fa-solid fa-sliders"></i> Stock Adjustments</h3>
                        <button class="btn btn-secondary" onclick="openModal('adjustment')"><i class="fa-solid fa-plus"></i> New Adjustment</button>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Adj Ref</th>
                                <th>Date</th>
                                <th>Product</th>
                                <th>System Qty</th>
                                <th>Physical Qty</th>
                                <th>Variance</th>
                                <th>Reason</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                appData.adjustments.forEach(a => {
                    const diffColor = a.diff >= 0 ? 'var(--success)' : 'var(--danger)';
                    html += `
                        <tr>
                            <td><strong>${a.name}</strong></td>
                            <td>${a.date}</td>
                            <td>${a.product_name}</td>
                            <td>${a.old_qty}</td>
                            <td><strong>${a.new_qty}</strong></td>
                            <td><strong style="color:${diffColor};">${a.diff > 0 ? '+' : ''}${a.diff}</strong></td>
                            <td>${a.reason}</td>
                        </tr>
                    `;
                });
                if (appData.adjustments.length === 0) {
                    html += `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No physical inventory count adjustments logged yet.</td></tr>`;
                }
                html += `</tbody></table>`;
                container.innerHTML = html;
            } else if (currentTab === 'ledger') {
                let html = `
                    <div class="panel-header">
                        <h3><i class="fa-solid fa-receipt"></i> Stock Audit Trail Ledger</h3>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Ref</th>
                                <th>Product</th>
                                <th>SKU</th>
                                <th>Type</th>
                                <th>From</th>
                                <th>To</th>
                                <th>Qty</th>
                                <th>User</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                appData.ledger.forEach(l => {
                    const typeBadge = {
                        'receipt': 'badge-success',
                        'delivery': 'badge-danger',
                        'transfer': 'badge-primary',
                        'adjustment': 'badge-warning'
                    }[l.type] || 'badge-primary';

                    html += `
                        <tr>
                            <td style="font-size:0.8rem; color:var(--text-muted);">${l.date}</td>
                            <td><strong>${l.ref}</strong></td>
                            <td>${l.product_name}</td>
                            <td><code>${l.sku}</code></td>
                            <td><span class="badge ${typeBadge}">${l.type.toUpperCase()}</span></td>
                            <td>${l.source}</td>
                            <td>${l.destination}</td>
                            <td><strong>${l.qty}</strong></td>
                            <td>${l.user}</td>
                        </tr>
                    `;
                });
                html += `</tbody></table>`;
                container.innerHTML = html;
            }
        }

        function filterProducts(query) {
            const q = query.toLowerCase();
            const rows = document.querySelectorAll('#product-rows tr');
            rows.forEach(r => {
                const text = r.innerText.toLowerCase();
                r.style.display = text.includes(q) ? '' : 'none';
            });
        }

        function openModal(type, targetId = null) {
            const overlay = document.getElementById('modal-overlay');
            const title = document.getElementById('modal-title');
            const body = document.getElementById('modal-body');

            if (type === 'receipt') {
                title.innerText = "Record Incoming Goods Receipt";
                let prodOptions = appData.products.map(p => `<option value="${p.id}">${p.name} (${p.sku})</option>`).join('');
                body.innerHTML = `
                    <div class="form-group">
                        <label>Supplier</label>
                        <select id="m-supplier"><option value="1">ABC Corporation</option></select>
                    </div>
                    <div class="form-group">
                        <label>Product</label>
                        <select id="m-product">${prodOptions}</select>
                    </div>
                    <div class="form-group">
                        <label>Quantity Received</label>
                        <input type="number" id="m-qty" value="10" min="1">
                    </div>
                    <div class="form-group">
                        <label>Notes</label>
                        <textarea id="m-notes" placeholder="Receipt notes..."></textarea>
                    </div>
                    <button class="btn btn-primary" onclick="submitReceipt()"><i class="fa-solid fa-check"></i> Validate Receipt</button>
                `;
            } else if (type === 'delivery') {
                title.innerText = "Create Outgoing Delivery Order";
                let prodOptions = appData.products.map(p => `<option value="${p.id}">${p.name} (In Stock: ${p.qty_available})</option>`).join('');
                body.innerHTML = `
                    <div class="form-group">
                        <label>Customer</label>
                        <select id="m-customer"><option value="1">XYZ Limited</option></select>
                    </div>
                    <div class="form-group">
                        <label>Product</label>
                        <select id="m-product">${prodOptions}</select>
                    </div>
                    <div class="form-group">
                        <label>Quantity to Ship</label>
                        <input type="number" id="m-qty" value="1" min="1">
                    </div>
                    <div class="form-group">
                        <label>Delivery Notes</label>
                        <textarea id="m-notes" placeholder="Shipping notes..."></textarea>
                    </div>
                    <button class="btn btn-primary" style="background: linear-gradient(135deg, var(--accent), #0284c7);" onclick="submitDelivery()"><i class="fa-solid fa-paper-plane"></i> Dispatch Stock</button>
                `;
            } else if (type === 'adjustment') {
                title.innerText = "Stock Count Adjustment";
                let prodOptions = appData.products.map(p => `<option value="${p.id}" ${p.id === targetId ? 'selected' : ''}>${p.name} (System Qty: ${p.qty_available})</option>`).join('');
                body.innerHTML = `
                    <div class="form-group">
                        <label>Product to Adjust</label>
                        <select id="m-product">${prodOptions}</select>
                    </div>
                    <div class="form-group">
                        <label>Physical Counted Quantity</label>
                        <input type="number" id="m-physical-qty" value="10" min="0">
                    </div>
                    <div class="form-group">
                        <label>Variance Reason</label>
                        <select id="m-reason">
                            <option value="Physical Count Variance">Physical Count Variance</option>
                            <option value="Damaged Goods">Damaged Goods</option>
                            <option value="Obsolete Stock">Obsolete Stock</option>
                            <option value="Loss / Theft">Loss / Theft</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" onclick="submitAdjustment()"><i class="fa-solid fa-sliders"></i> Apply Adjustment</button>
                `;
            } else if (type === 'product') {
                title.innerText = "Create New Product";
                body.innerHTML = `
                    <div class="form-group"><label>Product Name</label><input type="text" id="m-pname" placeholder="e.g. Fiber Cable"></div>
                    <div class="form-group"><label>SKU Code</label><input type="text" id="m-psku" placeholder="e.g. FC-007"></div>
                    <div class="form-group"><label>Category</label><select id="m-pcat"><option value="1">Raw Materials</option><option value="2">Office Equipment</option><option value="3">Electronics</option></select></div>
                    <div class="form-group"><label>Unit Price ($)</label><input type="number" id="m-pprice" value="100.00"></div>
                    <div class="form-group"><label>Initial Stock</label><input type="number" id="m-pstock" value="25"></div>
                    <button class="btn btn-primary" onclick="submitProduct()"><i class="fa-solid fa-plus"></i> Save Product</button>
                `;
            } else if (type === 'transfer') {
                title.innerText = "Internal Stock Transfer";
                let prodOptions = appData.products.map(p => `<option value="${p.id}">${p.name} (${p.sku})</option>`).join('');
                body.innerHTML = `
                    <div class="form-group"><label>Source Warehouse</label><select id="m-src"><option>Main Warehouse</option><option>Secondary Warehouse</option></select></div>
                    <div class="form-group"><label>Destination Warehouse</label><select id="m-dest"><option>Production Floor</option><option>Main Warehouse</option></select></div>
                    <div class="form-group"><label>Product</label><select id="m-product">${prodOptions}</select></div>
                    <div class="form-group"><label>Transfer Qty</label><input type="number" id="m-qty" value="5" min="1"></div>
                    <button class="btn btn-primary" onclick="submitTransfer()"><i class="fa-solid fa-arrow-right-arrow-left"></i> Execute Transfer</button>
                `;
            }

            overlay.classList.add('active');
        }

        function closeModal() {
            document.getElementById('modal-overlay').classList.remove('active');
        }

        async function submitReceipt() {
            const pid = document.getElementById('m-product').value;
            const qty = document.getElementById('m-qty').value;
            const notes = document.getElementById('m-notes').value;
            const res = await fetch('/api/receipt/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({supplier_id: 1, warehouse_id: 1, notes: notes, lines: [{product_id: pid, quantity: qty}]})
            });
            const data = await res.json();
            showToast(data.message);
            closeModal();
            fetchData();
        }

        async function submitDelivery() {
            const pid = document.getElementById('m-product').value;
            const qty = document.getElementById('m-qty').value;
            const notes = document.getElementById('m-notes').value;
            const res = await fetch('/api/delivery/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({customer_id: 1, warehouse_id: 1, notes: notes, lines: [{product_id: pid, quantity: qty}]})
            });
            const data = await res.json();
            if (!data.success) {
                alert(data.message);
                return;
            }
            showToast(data.message);
            closeModal();
            fetchData();
        }

        async function submitAdjustment() {
            const pid = document.getElementById('m-product').value;
            const physical_qty = document.getElementById('m-physical-qty').value;
            const reason = document.getElementById('m-reason').value;
            const res = await fetch('/api/adjustment/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({product_id: pid, physical_qty: physical_qty, reason: reason})
            });
            const data = await res.json();
            showToast(data.message);
            closeModal();
            fetchData();
        }

        async function submitProduct() {
            const name = document.getElementById('m-pname').value;
            const sku = document.getElementById('m-psku').value;
            const cat = document.getElementById('m-pcat').value;
            const price = document.getElementById('m-pprice').value;
            const stock = document.getElementById('m-pstock').value;
            const res = await fetch('/api/product/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name, sku: sku, category_id: cat, price: price, qty_available: stock})
            });
            const data = await res.json();
            showToast(data.message);
            closeModal();
            fetchData();
        }

        async function submitTransfer() {
            const src = document.getElementById('m-src').value;
            const dest = document.getElementById('m-dest').value;
            const pid = document.getElementById('m-product').value;
            const qty = document.getElementById('m-qty').value;
            const res = await fetch('/api/transfer/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({src_wh: src, dest_wh: dest, lines: [{product_id: pid, quantity: qty}]})
            });
            const data = await res.json();
            showToast(data.message);
            closeModal();
            fetchData();
        }

        function showToast(msg, isError = false) {
            const toast = document.getElementById('toast');
            document.getElementById('toast-msg').innerText = msg;
            toast.style.borderColor = isError ? 'var(--danger)' : 'var(--primary)';
            toast.style.display = 'flex';
            setTimeout(() => { toast.style.display = 'none'; }, 3500);
        }

        // Init
        fetchData();
    </script>
</body>
</html>
"""

def open_browser():
    time.sleep(1.2)
    webbrowser.open(f"http://localhost:{PORT}")

if __name__ == "__main__":
    print("===============================================================")
    print("  StockSense - Enterprise Inventory Management System Runner   ")
    print("===============================================================")
    print(f"Starting server on http://localhost:{PORT}...")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    server_address = ("", PORT)
    httpd = socketserver.TCPServer(server_address, StockSenseHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        sys.exit(0)
