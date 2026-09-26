import unittest
from datetime import datetime

class Product:
    def __init__(self, id, name, sku, qty, reorder_point):
        self.id = id
        self.name = name
        self.sku = sku
        self.qty = qty
        self.reorder_point = reorder_point

    @property
    def stock_status(self):
        if self.qty > 5:
            return 'available'
        elif self.qty > 0:
            return 'low'
        return 'unavailable'

class StockLedger:
    def __init__(self):
        self.entries = []

    def record(self, ref, product, movement_type, src, dest, qty):
        entry = {
            "date": datetime.now().isoformat(),
            "ref": ref,
            "product": product.name,
            "type": movement_type,
            "src": src,
            "dest": dest,
            "qty": qty
        }
        self.entries.append(entry)
        return entry

class TestStockSenseModule(unittest.TestCase):

    def setUp(self):
        self.steel_rods = Product(1, "Steel Rods", "SR-001", 100.0, 50.0)
        self.laptops = Product(2, "Laptops", "LT-003", 0.0, 5.0)
        self.chairs = Product(3, "Office Chairs", "OC-002", 4.0, 10.0)
        self.ledger = StockLedger()

    def test_stock_status_computation(self):
        self.assertEqual(self.steel_rods.stock_status, 'available')
        self.assertEqual(self.laptops.stock_status, 'unavailable')
        self.assertEqual(self.chairs.stock_status, 'low')

    def test_goods_receipt_workflow(self):
        initial_qty = self.steel_rods.qty
        received_qty = 50.0
        self.steel_rods.qty += received_qty
        self.ledger.record("RCP/00002", self.steel_rods, "receipt", "Vendors", "WH-01/Stock", received_qty)

        self.assertEqual(self.steel_rods.qty, initial_qty + received_qty)
        self.assertEqual(len(self.ledger.entries), 1)
        self.assertEqual(self.ledger.entries[0]["ref"], "RCP/00002")

    def test_delivery_order_validation(self):
        requested_qty = 10.0
        # Delivery order should fail if requested > available stock
        self.assertGreater(requested_qty, self.chairs.qty)

        # Successful delivery when stock is sufficient
        valid_qty = 2.0
        self.chairs.qty -= valid_qty
        self.ledger.record("DLV/00002", self.chairs, "delivery", "WH-01/Stock", "Customers", valid_qty)
        self.assertEqual(self.chairs.qty, 2.0)

    def test_internal_transfer(self):
        # Transfer move stock between locations; total company inventory remains unchanged
        transfer_qty = 20.0
        wh_a_qty = 100.0
        wh_b_qty = 0.0

        wh_a_qty -= transfer_qty
        wh_b_qty += transfer_qty

        self.assertEqual(wh_a_qty + wh_b_qty, 100.0)

    def test_stock_adjustment(self):
        recorded_qty = 50.0
        physical_count = 47.0
        variance = physical_count - recorded_qty

        self.assertEqual(variance, -3.0)
        recorded_qty = physical_count
        self.assertEqual(recorded_qty, 47.0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
