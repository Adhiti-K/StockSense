from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class StockSenseAdjustment(models.Model):
    _name = 'stocksense.adjustment'
    _description = 'Stock Adjustment - Inventory Reconciliation'
    _order = 'adjustment_date desc, id desc'

    name = fields.Char(
        string='Adjustment Number',
        default=lambda self: self.env['ir.sequence'].next_by_code('stocksense.adjustment'),
        readonly=True
    )
    adjustment_date = fields.Datetime(
        string='Adjustment Date',
        default=lambda: datetime.now(),
        required=True
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        help='Warehouse where adjustment is made'
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        required=True,
        help='Location where adjustment is made'
    )
    adjustment_line_ids = fields.One2many(
        'stocksense.adjustment.line',
        'adjustment_id',
        string='Adjustment Lines',
        copy=True
    )
    reason = fields.Selection(
        [
            ('damage', 'Damage'),
            ('loss', 'Loss/Theft'),
            ('count_variance', 'Count Variance'),
            ('obsolete', 'Obsolete'),
            ('other', 'Other'),
        ],
        string='Reason',
        required=True,
        help='Reason for adjustment'
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('reviewed', 'Reviewed'),
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
        help='Adjustment notes and remarks'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True
    )
    reviewed_by = fields.Many2one(
        'res.users',
        string='Reviewed By',
        help='User who reviewed the adjustment'
    )
    total_variance = fields.Float(
        string='Total Variance',
        compute='_compute_total_variance',
        store=True,
        help='Sum of all quantity variances'
    )

    @api.depends('adjustment_line_ids.quantity_variance')
    def _compute_total_variance(self):
        for record in self:
            record.total_variance = sum(record.adjustment_line_ids.mapped('quantity_variance'))

    def action_review(self):
        """Mark adjustment as reviewed"""
        for adjustment in self:
            if adjustment.state != 'draft':
                raise ValidationError('Only draft adjustments can be reviewed.')
            
            if not adjustment.adjustment_line_ids:
                raise ValidationError('Adjustment must have at least one line.')
            
            adjustment.reviewed_by = self.env.user
            adjustment.state = 'reviewed'

    def action_done(self):
        """Complete adjustment and update stock"""
        for adjustment in self:
            if adjustment.state != 'reviewed':
                raise ValidationError('Adjustment must be reviewed before completion.')
            
            # Create stock moves for each adjustment line
            for line in adjustment.adjustment_line_ids:
                if line.quantity_variance != 0:
                    # Determine source and destination based on variance
                    if line.quantity_variance > 0:
                        # Stock increase
                        source_loc = self.env.ref('stock.stock_location_inventory')
                        dest_loc = adjustment.location_id
                        qty = line.quantity_variance
                    else:
                        # Stock decrease
                        source_loc = adjustment.location_id
                        dest_loc = self.env.ref('stock.stock_location_inventory')
                        qty = abs(line.quantity_variance)
                    
                    # Create stock move
                    move = self.env['stock.move'].create({
                        'name': f"Adjustment: {adjustment.name} - {line.product_id.name}",
                        'product_id': line.product_id.id,
                        'product_uom_qty': qty,
                        'product_uom': line.uom_id.id,
                        'location_id': source_loc.id,
                        'location_dest_id': dest_loc.id,
                        'warehouse_id': adjustment.warehouse_id.id,
                        'origin': adjustment.name,
                    })
                    
                    # Mark as done
                    move.quantity_done = move.product_uom_qty
                    if move.state != 'done':
                        move._action_done()
                    
                    # Create stock ledger entry
                    self.env['stocksense.ledger'].create({
                        'product_id': line.product_id.id,
                        'movement_type': 'adjustment',
                        'quantity': line.quantity_variance,
                        'source_location_id': source_loc.id,
                        'destination_location_id': dest_loc.id,
                        'reference_doc': adjustment.name,
                        'notes': f"Reason: {adjustment.reason}. {adjustment.notes}",
                    })
            
            adjustment.state = 'done'

    def action_cancel(self):
        """Cancel the adjustment"""
        for adjustment in self:
            if adjustment.state == 'done':
                raise ValidationError('Cannot cancel a completed adjustment.')
            adjustment.state = 'canceled'

    def action_reset(self):
        """Reset to draft state"""
        for adjustment in self:
            if adjustment.state != 'canceled':
                raise ValidationError('Only canceled adjustments can be reset.')
            adjustment.state = 'draft'
            adjustment.reviewed_by = None


class StockSenseAdjustmentLine(models.Model):
    _name = 'stocksense.adjustment.line'
    _description = 'Adjustment Line Item'

    adjustment_id = fields.Many2one(
        'stocksense.adjustment',
        string='Adjustment',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )
    recorded_qty = fields.Float(
        string='Recorded Quantity',
        required=True,
        default=0.0,
        help='Quantity in system'
    )
    physical_qty = fields.Float(
        string='Physical Count',
        required=True,
        default=0.0,
        help='Actual quantity counted'
    )
    quantity_variance = fields.Float(
        string='Variance',
        compute='_compute_variance',
        store=True,
        help='Difference between physical and recorded'
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True,
        related='product_id.uom_id'
    )
    notes = fields.Text(
        string='Notes'
    )

    @api.depends('physical_qty', 'recorded_qty')
    def _compute_variance(self):
        for line in self:
            line.quantity_variance = line.physical_qty - line.recorded_qty

    @api.constrains('recorded_qty', 'physical_qty')
    def _check_quantities(self):
        for line in self:
            if line.recorded_qty < 0 or line.physical_qty < 0:
                raise ValidationError('Quantities must be non-negative.')