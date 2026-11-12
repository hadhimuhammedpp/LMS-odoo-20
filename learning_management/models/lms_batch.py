# -*- coding: utf-8 -*-
from odoo import api,fields,models
from odoo import Command
from odoo.orm.decorators import readonly

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
    color = fields.Integer(string='Color')
    company_id = fields.Many2one('res.company', string='Company', default= lambda self: self.env.user.company_id)
    state=fields.Selection([('draft','Draft'),('ongoing','Ongoing'),('completed','Completed'),('cancelled','Cancelled')], default='draft',string='State', tracking=True)
    student_count=fields.Integer(string='Registrations', compute='compute_student_count')
    scholarship_ids=fields.One2many('lms.scholarship',string='Scholarships', compute='compute_scholarship_ids', readonly=True)

    # view students count in smart button
    @api.depends('enrollment_ids.refference_id')
    def compute_student_count(self):
        for record in self:
            record.student_count = len(record.enrollment_ids)

    # students enrolled list view
    def students_enrolled (self):
        return{
            'type': 'ir.actions.act_window',
            'name': 'Student Enrolled',
            'res_model': 'res.partner',
            'view_mode': 'list',
            'domain':[('id','in',self.enrollment_ids.mapped('refference_id').ids)]
        }

    # modified list view of students scholarships records
    @api.depends('enrollment_ids','enrollment_ids.scholarship_ids','enrollment_ids.scholarship_ids.state')
    def compute_scholarship_ids(self):
        for record in self:
            scholarships = record.enrollment_ids.mapped('scholarship_ids').filtered(lambda s: s.state == 'fully approved')
            record.scholarship_ids = [Command.set(scholarships.ids)]
            print(scholarships.ids)

    # def start_button (self):
    #     for record in self:
    #         record.state = 'ongoing'
    # def complete_button (self):
    #     for record in self:
    #         record.state = 'completed'
    # def cancel_button (self):
    #     for record in self:
    #         record.state = 'cancelled'

