from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StockSenseProduct(models.Model):
    _inherit = 'product.product'

    stocksense_sku = fields.Char(
        string='SKU Code',
        help='Unique Stock Keeping Unit identifier'
    )
    stocksense_category_id = fields.Many2one(
        'stocksense.product.category',
        string='StockSense Category',
        help='Product category for StockSense'
    )
    reorder_qty = fields.Float(
        string='Reorder Quantity',
        default=0.0,
        help='Quantity at which product should be reordered'
    )
    reorder_point = fields.Float(
        string='Reorder Point',
        default=0.0,
        help='Stock level below which to trigger reorder'
    )
    stock_status = fields.Selection(
        [
            ('available', 'Available'),
            ('low', 'Low Stock'),
            ('unavailable', 'Out of Stock'),
        ],
        string='Stock Status',
        compute='_compute_stock_status',
        store=True,
        help='Current stock status based on quantity'
    )

    @api.depends('qty_available')
    def _compute_stock_status(self):
        """Compute stock status based on quantity available"""
        for record in self:
            qty = record.qty_available
            if qty > 5:
                record.stock_status = 'available'
            elif qty > 0:
                record.stock_status = 'low'
            else:
                record.stock_status = 'unavailable'

    def get_location_stock(self, location_id):
        """Get stock quantity for a specific location"""
        self.ensure_one()
        stock_move = self.env['stock.move'].search([
            ('product_id', '=', self.id),
            ('location_dest_id', '=', location_id),
            ('state', '=', 'done'),
        ])
        return sum(stock_move.mapped('quantity_done'))

    @api.constrains('reorder_qty', 'reorder_point')
    def _check_reorder_values(self):
        """Validate reorder quantities"""
        for record in self:
            if record.reorder_qty < 0 or record.reorder_point < 0:
                raise ValidationError('Reorder quantity and point must be non-negative.')


class StockSenseProductCategory(models.Model):
    _name = 'stocksense.product.category'
    _description = 'StockSense Product Category'

    name = fields.Char(
        string='Category Name',
        required=True,
        help='Name of the product category'
    )
    description = fields.Text(
        string='Description',
        help='Description of the category'
    )
    product_ids = fields.One2many(
        'product.product',
        'stocksense_category_id',
        string='Products'
    )

    def _sql_constraints(self):
        return [
            ('name_uniq', 'unique (name)', 'Category name must be unique!'),
        ]