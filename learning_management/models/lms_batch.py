# -*- coding: utf-8 -*-
from odoo import api,fields,models
from odoo.http import request

class LmsBatch(models.Model):
    _name = 'lms.batch'
    _description = 'Batch'
    _rec_name = 'batch_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    batch_name = fields.Char(string='Batch Name', required=True)
    enrollment_ids = fields.Many2many('lms.enrollment','batch_id', string='Enrollment IDs',)
    capacity = fields.Integer(string='Capacity', required=True, tracking=True)
    course_id =fields.Many2one('product.product', string='Course ID')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    company_id = fields.Many2one('res.company', string='Company', default= lambda self: self.env.user.company_id)
    state=fields.Selection([('draft','Draft'),('ongoing','Ongoing'),('completed','Completed'),('cancelled','Cancelled')], default='draft',string='State', tracking=True)
    student_count=fields.Integer(string='Registrations', compute='_compute_student_count', store=True)

    def start_button (self):
        for record in self:
            record.state = 'ongoing'
    def complete_button (self):
        for record in self:
            record.state = 'completed'
    def cancel_button (self):
        for record in self:
            record.state = 'cancelled'

    @api.depends('enrollment_ids.student_id')
    def _compute_student_count(self):
        for record in self:
            record.student_count = len(record.enrollment_ids.mapped('student_id'))

    def students_enrolled (self):
        return{
            'type': 'ir.actions.act_window',
            'name': 'Student Enrolled',
            'res_model': 'res.partner',
            'view_mode': 'list',
            'domain':[('id','in',self.enrollment_ids.mapped('student_id').ids)]
        }

