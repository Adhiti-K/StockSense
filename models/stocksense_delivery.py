from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class StockSenseDelivery(models.Model):
    _name = 'stocksense.delivery'
    _description = 'Stock Delivery - Outgoing Goods'
    _order = 'delivery_date desc, id desc'

    name = fields.Char(
        string='Delivery Number',
        default=lambda self: self.env['ir.sequence'].next_by_code('stocksense.delivery'),
        readonly=True
    )
    delivery_date = fields.Datetime(
        string='Delivery Date',
        default=lambda: datetime.now(),
        required=True
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        domain=[('customer_rank', '>', 0)],
        help='Customer receiving the goods'
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        help='Source warehouse for delivery'
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        required=True,
        help='Source location within warehouse'
    )
    delivery_line_ids = fields.One2many(
        'stocksense.delivery.line',
        'delivery_id',
        string='Delivery Lines',
        copy=True
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('ready', 'Ready'),
            ('in_transit', 'In Transit'),
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
        help='Additional notes for this delivery'
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

    @api.depends('delivery_line_ids.quantity')
    def _compute_total_items(self):
        for record in self:
            record.total_items = sum(record.delivery_line_ids.mapped('quantity'))

    def _check_stock_availability(self):
        """Verify all items are in stock"""
        for delivery in self:
            for line in delivery.delivery_line_ids:
                available_qty = line.product_id.with_context(
                    location=delivery.location_id.id
                ).qty_available
                
                if available_qty < line.quantity:
                    raise ValidationError(
                        f"Insufficient stock for {line.product_id.name}. "
                        f"Required: {line.quantity}, Available: {available_qty}"
                    )

    def action_confirm(self):
        """Confirm delivery and check stock availability"""
        for delivery in self:
            if delivery.state != 'draft':
                raise ValidationError('Only draft deliveries can be confirmed.')
            
            if not delivery.delivery_line_ids:
                raise ValidationError('Delivery must have at least one line.')
            
            delivery._check_stock_availability()
            delivery.state = 'ready'

    def action_pick(self):
        """Mark items as picked"""
        for delivery in self:
            if delivery.state not in ['draft', 'ready']:
                raise ValidationError('Delivery must be in draft or ready state to pick.')
            delivery.state = 'ready'

    def action_ship(self):
        """Mark delivery as in transit"""
        for delivery in self:
            if delivery.state != 'ready':
                raise ValidationError('Delivery must be ready before shipping.')
            delivery.state = 'in_transit'

    def action_done(self):
        """Complete delivery and reduce stock"""
        for delivery in self:
            if delivery.state != 'in_transit':
                raise ValidationError('Delivery must be in transit before completing.')
            
            delivery._check_stock_availability()
            
            # Create stock moves for each line
            for line in delivery.delivery_line_ids:
                self.env['stock.move'].create({
                    'name': f"Delivery: {delivery.name} - {line.product_id.name}",
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.uom_id.id,
                    'location_id': delivery.location_id.id,
                    'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                    'warehouse_id': delivery.warehouse_id.id,
                    'origin': delivery.name,
                })
                
                # Create stock ledger entry
                self.env['stocksense.ledger'].create({
                    'product_id': line.product_id.id,
                    'movement_type': 'delivery',
                    'quantity': -line.quantity,
                    'source_location_id': delivery.location_id.id,
                    'destination_location_id': self.env.ref('stock.stock_location_customers').id,
                    'reference_doc': delivery.name,
                    'notes': delivery.notes,
                })
            
            delivery.state = 'done'

    def action_cancel(self):
        """Cancel the delivery"""
        for delivery in self:
            if delivery.state == 'done':
                raise ValidationError('Cannot cancel a completed delivery.')
            delivery.state = 'canceled'

    def action_reset(self):
        """Reset to draft state"""
        for delivery in self:
            if delivery.state != 'canceled':
                raise ValidationError('Only canceled deliveries can be reset.')
            delivery.state = 'draft'


class StockSenseDeliveryLine(models.Model):
    _name = 'stocksense.delivery.line'
    _description = 'Delivery Line Item'

    delivery_id = fields.Many2one(
        'stocksense.delivery',
        string='Delivery',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )
    quantity = fields.Float(
        string='Quantity to Deliver',
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