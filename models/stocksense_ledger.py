from odoo import models, fields, api
from datetime import datetime


class StockSenseLedger(models.Model):
    _name = 'stocksense.ledger'
    _description = 'Stock Movement Ledger'
    _order = 'movement_date desc, id desc'

    movement_date = fields.Datetime(
        string='Movement Date',
        default=lambda: datetime.now(),
        required=True,
        index=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        index=True
    )
    sku = fields.Char(
        string='SKU',
        related='product_id.stocksense_sku',
        store=True
    )
    movement_type = fields.Selection(
        [
            ('receipt', 'Receipt'),
            ('delivery', 'Delivery'),
            ('internal_transfer', 'Internal Transfer'),
            ('adjustment', 'Adjustment'),
        ],
        string='Movement Type',
        required=True,
        index=True
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
        help='Quantity moved (positive or negative)'
    )
    source_location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        help='From where goods were moved'
    )
    destination_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        help='To where goods were moved'
    )
    reference_doc = fields.Char(
        string='Reference Document',
        help='Related receipt/delivery/transfer number'
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        readonly=True
    )
    notes = fields.Text(
        string='Notes'
    )
    balance = fields.Float(
        string='Running Balance',
        compute='_compute_balance',
        store=True,
        help='Cumulative stock quantity after this movement'
    )

    @api.depends('quantity')
    def _compute_balance(self):
        """Calculate running balance for each product"""
        for record in self:
            # Get all previous movements for same product
            previous_moves = self.search([
                ('product_id', '=', record.product_id.id),
                ('movement_date', '<', record.movement_date),
            ], order='movement_date asc, id asc')
            
            balance = sum(previous_moves.mapped('quantity'))
            record.balance = balance + record.quantity

    def get_product_history(self, product_id, location_id=None):
        """Get movement history for a product"""
        domain = [('product_id', '=', product_id)]
        
        if location_id:
            domain += [
                '|',
                ('source_location_id', '=', location_id),
                ('destination_location_id', '=', location_id),
            ]
        
        return self.search(domain, order='movement_date desc')

    def get_movements_by_type(self, movement_type, date_from=None, date_to=None):
        """Get movements filtered by type and date range"""
        domain = [('movement_type', '=', movement_type)]
        
        if date_from:
            domain += [('movement_date', '>=', date_from)]
        if date_to:
            domain += [('movement_date', '<=', date_to)]
        
        return self.search(domain, order='movement_date desc')

    def get_stock_valuation(self):
        """Get total stock valuation"""
        total_value = 0.0
        
        for ledger in self:
            product = ledger.product_id
            unit_cost = product.standard_price or 0.0
            total_value += ledger.quantity * unit_cost
        
        return total_value


class StockSenseLedgerSummary(models.Model):
    _name = 'stocksense.ledger.summary'
    _description = 'Stock Ledger Summary by Product'
    _auto = False

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        readonly=True
    )
    total_received = fields.Float(
        string='Total Received',
        readonly=True
    )
    total_delivered = fields.Float(
        string='Total Delivered',
        readonly=True
    )
    total_transferred = fields.Float(
        string='Total Transferred (In)',
        readonly=True
    )
    total_adjustments = fields.Float(
        string='Total Adjustments',
        readonly=True
    )
    net_movement = fields.Float(
        string='Net Movement',
        readonly=True
    )

    def init(self):
        """Create view for ledger summary"""
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW stocksense_ledger_summary AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY product_id) as id,
                    product_id,
                    COALESCE(SUM(CASE WHEN movement_type = 'receipt' THEN quantity ELSE 0 END), 0) as total_received,
                    COALESCE(SUM(CASE WHEN movement_type = 'delivery' THEN quantity ELSE 0 END), 0) as total_delivered,
                    COALESCE(SUM(CASE WHEN movement_type = 'internal_transfer' THEN quantity ELSE 0 END), 0) as total_transferred,
                    COALESCE(SUM(CASE WHEN movement_type = 'adjustment' THEN quantity ELSE 0 END), 0) as total_adjustments,
                    COALESCE(SUM(quantity), 0) as net_movement
                FROM stocksense_ledger
                GROUP BY product_id
            )
        """)