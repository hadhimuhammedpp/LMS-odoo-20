# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime,timedelta
from odoo.exceptions import UserError

class LmsScholarship(models.Model):
    _name='lms.scholarship'
    _description='Scholarship'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name=fields.Char(string="scholarship Name", tracking=True)
    enrollment_id=fields.Many2one('lms.enrollment',string="Enrollment id", required=True)
    course_id=fields.Many2one('product.product',string="Course id", related='enrollment_id.course_id')
    state=fields.Selection([('pending','Pending'), ('confirmed','Confirmed'), ('first approved','First Approved'),('fully approved','Fully Approved'), ('rejected','Rejected')],default="pending")
    student_id=fields.Many2one('res.partner',string="Student id", related='enrollment_id.student_id')
    due_date=fields.Date(string="Due date", default=fields.Date.today()+ timedelta(days=15))
    validity=fields.Integer(string="Validity")
    discount_amount=fields.Monetary(string="Discount amount", required=True)
    company_id=fields.Many2one('res.company',string="Company", default=lambda self: self.env.company)
    currency_id=fields.Many2one('res.currency',string="Currency", related='company_id.currency_id')

    def approve_button(self):
        for record in self:
            record.state='fully approved'
    def reject_button(self):
        for record in self:
            record.state='rejected'

    @api.constrains('discount_amount')
    def _discount_amount_constraint(self):
        for record in self:
            if record.discount_amount<0:
                raise UserError('Discount amount cannot be negative')



