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

    course_id = fields.Many2one('product.product',string='Course id', domain=[('categ_id','=','Education')], required=True, copy=False)
    name=fields.Char(string='Enrollment name', default=lambda self:('New'), copy=False)
    refference_id=fields.Many2one('res.partner',string='Reference id',copy=False, domain=[('is_student','!=', 'Active')], tracking=True)
    student_id=fields.Char(related='refference_id.name', string='Student ID', context={'show_address':1})
    date=fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    due_date=fields.Date(string='Due date', default=lambda self: fields.Date.today()+ timedelta(days=15))
    course_fee=fields.Float(string='Course Fee', related='course_id.list_price', tracking=True)
    is_lead=fields.Boolean(string='Is Lead', help="Is Lead", copy=False, tracking=True)
    description=fields.Text(string='Description')
    terms_and_conditions=fields.Html()
    state=fields.Selection([('draft','Draft'),('confirm','Confirm'),('done','Done'),('cancel','Cancel')],string='State', default='draft')
    company_id=fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id=fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    dob=fields.Date(string='Date of Birth', default=fields.Date.today())
    age=fields.Integer(string='Age', default=0, compute='compute_age')
    batch_id=fields.Many2one('lms.batch', string='Batch')
    image=fields.Image(string='Image')
    scholarship_ids=fields.One2many('lms.scholarship','enrollment_id', string='Scholarship ID')
    # sequence generation
    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if val.get('name','New')=="New":
                val['name']=self.env['ir.sequence'].next_by_code('lms.enrollment')
        return super(LmsEnrollment,self).create(vals)

    @api.constrains('course_fee')
    def course_fee_validation(self):
        for record in self:
                if record.course_fee==0:
                    raise UserError('The course fees cannot be zero')
    @api.constrains('dob')
    def dob_validation(self):
        for record in self:
            if record.dob>fields.Date.today():
                raise UserError('The DOB cannot be in the future')

    @api.constrains('date')
    def date_validation(self):
        for record in self:
            if record.date < fields.Date.today():
                raise UserError('The Date cannot be in the past')

    @api.constrains('student_id','course_id')
    def student_duplication_validation(self):
        for record in self:
            duplicate=self.search(['&',('student_id','=',record.student_id),('course_id','=',record.course_id),('id','!=',record.id)])
            if duplicate:
                raise UserError('The student id and course id cannot be the same')

    @api.depends('dob', 'age')
    def compute_age(self):
        for record in self:
            if record.dob:
                record.age=fields.Date.today().year-record.dob.year
                if fields.Date.today().month < record.dob.month:
                    record.age=record.age-1
                if record.age < 18:
                    raise UserError('The age should be greater than 18')

    def confirm_button(self):
        for record in self:
            record.state='confirm'
    def cancel_button(self):
        for record in self:
            record.state='cancel'
    def done_button(self):
        for record in self:
            record.state='done'
