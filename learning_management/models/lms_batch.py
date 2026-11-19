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
    course_id = fields.Many2one('product.product', string='Course ID', required=True, domain=[('categ_id', '=', 'Education')])
    start_date = fields.Date(string='Start Date', default=fields.Date.context_today, tracking=True)
    end_date = fields.Date(string='End Date')
    color = fields.Integer(string='Color')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    student_count = fields.Integer(string='Registrations', compute='compute_student_count')
    scholarship_ids = fields.One2many('lms.scholarship', string='Scholarships', compute='compute_scholarship_ids',readonly=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    invoice_count=fields.Integer(string='Invoice Count', compute='compute_invoice_count')
    to_be_invoiced=fields.Integer(string='To Be Invoiced', compute='compute_to_be_invoiced', readonly=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    total_revenue=fields.Monetary(string='Total Revenue', compute='compute_total_revenue', readonly=True, currency_field='currency_id')

    # view students count in smart button
    @api.depends('enrollment_ids.refference_id')
    def compute_student_count(self):
        for record in self:
            record.student_count = len(record.enrollment_ids)

    # view invoice count in smart button
    @api.depends('enrollment_ids.invoice_id')
    def compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.enrollment_ids.mapped('invoice_id'))

    # to find the number of un invoiced enrollments
    @api.depends('enrollment_ids', 'enrollment_ids.invoice_id')
    def compute_to_be_invoiced(self):
        for record in self:
            record.to_be_invoiced = len(record.enrollment_ids) - len(record.enrollment_ids.mapped('invoice_id'))
            # record.to_be_invoiced = len(record.enrollment_ids.filtered(lambda r: not r.invoice_id))

    # with state= fully approved list view of scholarships records
    @api.depends('enrollment_ids', 'enrollment_ids.scholarship_ids', 'enrollment_ids.scholarship_ids.state')
    def compute_scholarship_ids(self):
        for record in self:
            scholarships = record.enrollment_ids.mapped('scholarship_ids').filtered(
                lambda s: s.state == 'fully approved')
            record.scholarship_ids = [Command.set(scholarships.ids)]

    # function to compute the total revenue from batch (posted invoice state)
    @api.depends('enrollment_ids', 'enrollment_ids.invoice_id','enrollment_ids.invoice_id.amount_total','enrollment_ids.invoice_id.state')
    def compute_total_revenue(self):
        for record in self:
            invoices=record.enrollment_ids.mapped('invoice_id').filtered(lambda i: i.state=='posted')
            record.total_revenue = sum(invoices.mapped('amount_total'))

    # to validate number of enrollments and capacity
    @api.constrains('enrollment_ids', 'capacity')
    def check_enrollment_ids(self):
        for record in self:
            if len(record.enrollment_ids) > record.capacity:
                raise UserError('The total capacity is Full!')

    # to validate course_id of both enrollment and batch are same
    @api.constrains('course_id', 'enrollment_ids')
    def check_courses_in_batch_and_enrollments(self):
        for record in self:
            if record.enrollment_ids:
                if record.course_id != record.enrollment_ids.course_id:
                    raise UserError('The course and enrollment do not match!')

    # function of run billing button
    def run_billing_button(self):
        discount_product = self.env.ref('learning_management.lms_scholarship')
        if not self.enrollment_ids:
            raise UserError('There are no enrollments in this batch')
        for record in self.enrollment_ids:
            if record.invoice_id:
                continue
            if record.state not in ['done', 'confirm']:
                continue
            course_fee = record.course_fee
            approved_scholarships = record.scholarship_ids.filtered(lambda s: s.state == 'fully approved')
            total_discount = sum(approved_scholarships.mapped('discount_amount'))
            if total_discount > course_fee:
                raise UserError('The discount amount cannot be greater than the course fee')
            # self.enrollment_ids.cron_generate_due_invoices()
            invoice_lines = [Command.create({
                    'product_id': record.course_id.id,
                    'name': record.course_id.display_name,
                    'quantity': 1,
                    'price_unit': course_fee
                })]
            if total_discount > 0:
                invoice_lines.append(Command.create({
                    'product_id': discount_product.id,
                    'name': 'scholarship discount',
                    'quantity': 1,
                    'price_unit': -total_discount
                }))
            invoice = self.env['account.move'].create({'move_type': 'out_invoice',
                                                       'partner_id': record.refference_id.id,
                                                       'invoice_date': fields.Date.context_today(record),
                                                       'company_id': record.company_id.id,
                                                       'invoice_origin': record.name,
                                                       'invoice_line_ids': invoice_lines,
                                                       'lms_enrollment_id': record.id
                                                       })
            invoice.action_post()
            record.sudo().write({'invoice_id': invoice.id})
            if invoice.partner_id.email:
                template=self.env.ref('learning_management.mail_template_lms_invoice')
                template.send_mail(invoice.id, force_send=True)
                record.message_post(body="the invoice has been sent successfully!", message_type='tracking')
            # record.invoice_id = invoice.id
            # self.write({'state':'completed'})

    # students enrolled list view in smart button
    def students_enrolled(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Student Enrolled',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.enrollment_ids.mapped('refference_id').ids)]}

    # invoices smart button view in batch
    def invoices_button(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'invoices button',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.enrollment_ids.mapped('invoice_id').ids)]
        }



