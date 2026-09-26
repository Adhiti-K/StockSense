from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class StockSenseTransfer(models.Model):
    _name = 'stocksense.transfer'
    _description = 'Internal Stock Transfer'
    _order = 'transfer_date desc, id desc'

    name = fields.Char(
        string='Transfer Number',
        default=lambda self: self.env['ir.sequence'].next_by_code('stocksense.transfer'),
        readonly=True
    )
    transfer_date = fields.Datetime(
        string='Transfer Date',
        default=lambda: datetime.now(),
        required=True
    )
    source_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Source Warehouse',
        required=True,
        help='Warehouse from which goods are transferred'
    )
    source_location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        required=True,
        help='Source location within warehouse'
    )
    destination_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Destination Warehouse',
        required=True,
        help='Warehouse to which goods are transferred'
    )
    destination_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        required=True,
        help='Destination location within warehouse'
    )
    transfer_line_ids = fields.One2many(
        'stocksense.transfer.line',
        'transfer_id',
        string='Transfer Lines',
        copy=True
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
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
        help='Additional notes for this transfer'
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

    @api.depends('transfer_line_ids.quantity')
    def _compute_total_items(self):
        for record in self:
            record.total_items = sum(record.transfer_line_ids.mapped('quantity'))

    @api.constrains('source_location_id', 'destination_location_id')
    def _check_locations_different(self):
        for transfer in self:
            if transfer.source_location_id == transfer.destination_location_id:
                raise ValidationError('Source and destination locations must be different.')

    def _check_stock_availability(self):
        """Verify all items exist at source location"""
        for transfer in self:
            for line in transfer.transfer_line_ids:
                available_qty = line.product_id.with_context(
                    location=transfer.source_location_id.id
                ).qty_available
                
                if available_qty < line.quantity:
                    raise ValidationError(
                        f"Insufficient stock for {line.product_id.name} at source location. "
                        f"Required: {line.quantity}, Available: {available_qty}"
                    )

    def action_confirm(self):
        """Confirm transfer"""
        for transfer in self:
            if transfer.state != 'draft':
                raise ValidationError('Only draft transfers can be confirmed.')
            
            if not transfer.transfer_line_ids:
                raise ValidationError('Transfer must have at least one line.')
            
            transfer._check_stock_availability()
            transfer.state = 'confirmed'

    def action_start(self):
        """Start transfer (in transit)"""
        for transfer in self:
            if transfer.state != 'confirmed':
                raise ValidationError('Transfer must be confirmed before starting.')
            transfer.state = 'in_transit'

    def action_done(self):
        """Complete transfer and update stock locations"""
        for transfer in self:
            if transfer.state != 'in_transit':
                raise ValidationError('Transfer must be in transit to complete.')
            
            transfer._check_stock_availability()
            
            # Create stock moves for each line
            for line in transfer.transfer_line_ids:
                # Create stock move
                move = self.env['stock.move'].create({
                    'name': f"Transfer: {transfer.name} - {line.product_id.name}",
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.uom_id.id,
                    'location_id': transfer.source_location_id.id,
                    'location_dest_id': transfer.destination_location_id.id,
                    'warehouse_id': transfer.source_warehouse_id.id,
                    'origin': transfer.name,
                })
                
                # Mark as done
                move.quantity_done = move.product_uom_qty
                if move.state != 'done':
                    move._action_done()
                
                # Create stock ledger entry
                self.env['stocksense.ledger'].create({
                    'product_id': line.product_id.id,
                    'movement_type': 'internal_transfer',
                    'quantity': line.quantity,
                    'source_location_id': transfer.source_location_id.id,
                    'destination_location_id': transfer.destination_location_id.id,
                    'reference_doc': transfer.name,
                    'notes': transfer.notes,
                })
            
            transfer.state = 'done'

    def action_cancel(self):
        """Cancel the transfer"""
        for transfer in self:
            if transfer.state == 'done':
                raise ValidationError('Cannot cancel a completed transfer.')
            transfer.state = 'canceled'

    def action_reset(self):
        """Reset to draft state"""
        for transfer in self:
            if transfer.state != 'canceled':
                raise ValidationError('Only canceled transfers can be reset.')
            transfer.state = 'draft'


class StockSenseTransferLine(models.Model):
    _name = 'stocksense.transfer.line'
    _description = 'Transfer Line Item'

    transfer_id = fields.Many2one(
        'stocksense.transfer',
        string='Transfer',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )
    quantity = fields.Float(
        string='Quantity to Transfer',
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