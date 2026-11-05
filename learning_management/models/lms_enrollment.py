# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError
import re

class LmsEnrollment(models.Model):
    _name = 'lms.enrollment'
    _description = 'Enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    course_id = fields.Many2one('product.product',string='Course id', domain=[('type','=','service')], required=True)
    name=fields.Char(string='Enrollment id', default='New')
    reference_id=fields.Char(string='Reference id', required=True)
    student_id=fields.Many2one('res.partner', string='Student ID', context={'show_address':1}, required=True)
    date=fields.Date(string='Date', default=fields.Date.today(), required=True)
    due_date=fields.Date(string='Due date', default=fields.Date.today()+ timedelta(days=15))
    course_fee=fields.Monetary(string='Course Fee')
    is_lead=fields.Boolean(string='Is Lead')
    description=fields.Text(string='Description')
    terms_and_conditions=fields.Html()
    state=fields.Selection([('draft','Draft'),('confirm','Confirm'),('done','Done'),('cancel','Cancel')],string='State', default='draft')
    company_id=fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id=fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    dob=fields.Date(string='Date of Birth', default=fields.Date.today())
    age=fields.Integer(string='Age', default=0, compute='compute_age')

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if val.get('name','New')=="New":
                val['name']=self.env['ir.sequence'].next_by_code('lms.enrollment')
        return super(LmsEnrollment,self).create(vals_list)

    @api.constrains('reference_id')
    def check_reference_id(self):
        pattern = '^(?=(?:.*[a-zA-Z]){3})(?=(?:.*\d){3})(?=(?:.*[^a-zA-Z0-9]){2})'
        for record in self:
            if record.reference_id:
               if not re.match(pattern,record.reference_id):
                   raise UserError('the reference id should contains 3 alphabets, 3 numbers and 2 special characters.')

    @api.depends('dob')
    def compute_age(self):
        for record in self:
            if record.dob:
                record.age=fields.Date.today().year-record.dob.year

    def confirm_button(self):
        for record in self:
            record.state='confirm'
    def cancel_button(self):
        for record in self:
            record.state='cancel'
