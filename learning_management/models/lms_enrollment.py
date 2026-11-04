# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import timedelta

class LmsEnrollment(models.Model):
    _name = 'lms.enrollment'
    _description = 'Lms.Enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    course_id = fields.Many2one('product.product',string='Course id')
    name=fields.Char(string='Name', required=True)
    student_id=fields.Many2one('res.partner', string='Student ID')
    date=fields.Date(string='Date', default=fields.Date.today())
    due_date=fields.Date(string='Due date', compute='compute_duedate')
    course_fee=fields.Float(string='Course Fee', related='course_id.lst_price')
    is_lead=fields.Boolean(string='Is Lead')
    description=fields.Text(string='Description')
    terms_and_conditions=fields.Html()
    state=fields.Selection([('draft','Draft'),('confirm','Confirm'),('done','Done'),('cancel','Cancel')],string='State', default='draft')

    def compute_duedate(self):
        for record in self:
                record.due_date = fields.Date.today()+timedelta(days=15)
