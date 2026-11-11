# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime,timedelta
from odoo.exceptions import UserError

class LmsScholarship(models.Model):
    _name='lms.scholarship'
    _description='Scholarship'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name=fields.Char(string="scholarship Name", tracking=True)
    enrollment_id=fields.Many2one('lms.enrollment',string="Enrollment id", required=True, tracking=True)
    course_id=fields.Many2one('product.product',string="Course id", related='enrollment_id.course_id')
    state=fields.Selection([('pending','Pending'), ('confirmed','Confirmed'), ('first approved','First Approved'),('fully approved','Fully Approved'), ('rejected','Rejected')],default="pending")
    student_id=fields.Many2one('res.partner',string="Student id", tracking=True)
    due_date=fields.Date(string="Due date", compute="compute_due_date", inverse="inverse_due_date")
    validity=fields.Integer(string="Validity", default=1)
    discount_amount=fields.Monetary(string="Discount amount", required=True, tracking=True)
    company_id=fields.Many2one('res.company',string="Company", default=lambda self: self.env.company)
    currency_id=fields.Many2one('res.currency',string="Currency", related='company_id.currency_id')

    @api.depends('validity','due_date')
    def compute_due_date(self):
        for record in self:
            record.due_date=fields.Date.today()+timedelta(days=record.validity)
    def inverse_due_date(self):
        for record in self:
            record.validity=(record.due_date-fields.Date.today()).days

    def approve_button(self):
        for record in self:
            record.state='fully approved'
    def reject_button(self):
        for record in self:
            record.state='rejected'
    def first_approve_button(self):
        for record in self:
            record.state='first approved'
    def confirm_button(self):
            for record in self:
                record.state = 'confirmed'

    @api.constrains('discount_amount')
    def discount_amount_constraint(self):
        for record in self:
            if record.discount_amount>record.course_id.list_price:
                raise UserError('The Discount amount cannot be greater than the course price')
            elif record.discount_amount<0:
                raise UserError('The Discount amount cannot be less than 0')
            elif record.discount_amount==0:
                raise UserError('The Discount amount cannot be 0')



