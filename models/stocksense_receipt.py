from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class StockSenseReceipt(models.Model):
    _name = 'stocksense.receipt'
    _description = 'Stock Receipt - Incoming Goods'
    _order = 'receipt_date desc, id desc'

    name = fields.Char(
        string='Receipt Number',
        default=lambda self: self.env['ir.sequence'].next_by_code('stocksense.receipt'),
        readonly=True
    )
    receipt_date = fields.Datetime(
        string='Receipt Date',
        default=lambda: datetime.now(),
        required=True
    )
    supplier_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        required=True,
        domain=[('supplier_rank', '>', 0)],
        help='Supplier from whom goods are received'
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        help='Destination warehouse for received goods'
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        required=True,
        help='Destination location within warehouse'
    )
    receipt_line_ids = fields.One2many(
        'stocksense.receipt.line',
        'receipt_id',
        string='Receipt Lines',
        copy=True
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('canceled', 'Canceled'),
        ],
        string='State',
        default='draft',
        required=True,
        tracking=True
    )
    notes = fields.Text(
        string='Notes',
        help='Additional notes for this receipt'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True
    )
    total_items = fields.Integer(
        string='Total Items',
        compute='_compute_total_items',
        store=True
    )

    @api.depends('receipt_line_ids.quantity')
    def _compute_total_items(self):
        for record in self:
            record.total_items = sum(record.receipt_line_ids.mapped('quantity'))

    def action_confirm(self):
        """Confirm receipt and create stock moves"""
        for receipt in self:
            if receipt.state != 'draft':
                raise ValidationError('Only draft receipts can be confirmed.')
            
            if not receipt.receipt_line_ids:
                raise ValidationError('Receipt must have at least one line.')
            
            receipt.state = 'confirmed'
            
            # Create stock moves
            for line in receipt.receipt_line_ids:
                self.env['stock.move'].create({
                    'name': f"Receipt: {receipt.name} - {line.product_id.name}",
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.uom_id.id,
                    'location_id': self.env.ref('stock.stock_location_suppliers').id,
                    'location_dest_id': receipt.location_id.id,
                    'warehouse_id': receipt.warehouse_id.id,
                    'origin': receipt.name,
                })
            
            # Create stock ledger entry
            self.env['stocksense.ledger'].create({
                'product_id': line.product_id.id,
                'movement_type': 'receipt',
                'quantity': line.quantity,
                'source_location_id': self.env.ref('stock.stock_location_suppliers').id,
                'destination_location_id': receipt.location_id.id,
                'reference_doc': receipt.name,
                'notes': receipt.notes,
            })

    def action_done(self):
        """Complete the receipt"""
        for receipt in self:
            if receipt.state != 'confirmed':
                raise ValidationError('Only confirmed receipts can be done.')
            
            # Mark all stock moves as done
            stock_moves = self.env['stock.move'].search([
                ('origin', '=', receipt.name),
            ])
            for move in stock_moves:
                move.quantity_done = move.product_uom_qty
                if move.state not in ['done', 'cancel']:
                    move._action_done()
            
            receipt.state = 'done'

    def action_cancel(self):
        """Cancel the receipt"""
        for receipt in self:
            if receipt.state == 'done':
                raise ValidationError('Cannot cancel a completed receipt.')
            
            # Cancel all related stock moves
            stock_moves = self.env['stock.move'].search([
                ('origin', '=', receipt.name),
                ('state', '!=', 'done'),
            ])
            stock_moves._action_cancel()
            
            receipt.state = 'canceled'

    def action_reset(self):
        """Reset to draft state"""
        for receipt in self:
            if receipt.state != 'canceled':
                raise ValidationError('Only canceled receipts can be reset.')
            receipt.state = 'draft'


class StockSenseReceiptLine(models.Model):
    _name = 'stocksense.receipt.line'
    _description = 'Receipt Line Item'

    receipt_id = fields.Many2one(
        'stocksense.receipt',
        string='Receipt',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )
    quantity = fields.Float(
        string='Quantity Received',
        required=True,
        default=1.0
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True,
        related='product_id.uom_id'
    )
    notes = fields.Text(
        string='Line Notes'
    )

    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError('Quantity must be greater than zero.')