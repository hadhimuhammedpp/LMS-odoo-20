# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo import Command
from odoo.exceptions import UserError
from odoo.orm.decorators import readonly

class LmsBatch(models.Model):
    _name = 'lms.batch'
    _description = 'Batch'
    _rec_name = 'batch_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    batch_name = fields.Char(string='Batch Name', required=True)
    enrollment_ids = fields.One2many('lms.enrollment', 'batch_id', string='Enrollment IDs', )
    capacity = fields.Integer(string='Capacity', required=True, tracking=True)
    course_id = fields.Many2one('product.product', string='Course ID')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    color = fields.Integer(string='Color')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    state = fields.Selection(
        [('ongoing', 'Ongoing'), ('completed', 'Completed')],default='ongoing', string='State', tracking=True)
    student_count = fields.Integer(string='Registrations', compute='compute_student_count')
    scholarship_ids = fields.One2many('lms.scholarship', string='Scholarships', compute='compute_scholarship_ids',
                                      readonly=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)

    # view students count in smart button
    @api.depends('enrollment_ids.refference_id')
    def compute_student_count(self):
        for record in self:
            record.student_count = len(record.enrollment_ids)

    # students enrolled list view
    def students_enrolled(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Student Enrolled',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.enrollment_ids.mapped('refference_id').ids)]}

    # invoices smart button in batch view
    def invoices_button(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'invoices button',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('partner_id', 'in', self.enrollment_ids.mapped('refference_id').ids)]
        }

    # modified list view of students scholarships records
    @api.depends('enrollment_ids', 'enrollment_ids.scholarship_ids', 'enrollment_ids.scholarship_ids.state')
    def compute_scholarship_ids(self):
        for record in self:
            scholarships = record.enrollment_ids.mapped('scholarship_ids').filtered(
                lambda s: s.state == 'fully approved')
            record.scholarship_ids = [Command.set(scholarships.ids)]

    # function of run billing button
    def run_billing_button(self):
        if not self.enrollment_ids:
            raise UserError('There are no enrollments in this batch')
        for record in self.enrollment_ids:
            if record.invoice_id:
                continue
            course_fee = record.course_fee
            approved_scholarships = record.scholarship_ids.filtered(lambda s: s.state == 'fully approved')
            total_discount = sum(approved_scholarships.mapped('discount_amount'))
            if total_discount > course_fee:
                raise UserError('The discount amount cannot be greater than the course fee')
            invoice = self.env['account.move'].create({'move_type': 'out_invoice',
                                                       'partner_id': record.refference_id.id,
                                                       'invoice_date': fields.Date.context_today(record),
                                                       'company_id': record.company_id.id,
                                                       'invoice_origin': record.name,
                                                       'invoice_line_ids': [
                                                           Command.create({'product_id': record.course_id.id,
                                                                           'name': record.course_id.display_name,
                                                                           'price_unit': course_fee,
                                                                           'quantity': 1,
                                                                           }),
                                                           Command.create({'product_id': record.course_id.id,
                                                                           'name': 'Scholarship Discount',
                                                                           'price_unit':-total_discount,
                                                                           'quantity': 1,
                                                                           })
                                                           ]
                                                       })
            record.invoice_id = invoice.id
            self.write({'active': False,'state':'completed'})

    def reset_to_draft_button(self):
        for record in self:
            record.state = 'ongoing'
