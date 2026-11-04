# -*- coding: utf-8 -*-
from odoo import models, fields

class LmsScholarship(models.Model):
    _name='lms.scholarship'
    _description='Lms.Scholarship'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name=fields.Char(string="Name")
    enrollment_id=fields.Many2one('lms.enrollment',string="Enrollment id")
    state=fields.Selection([('pending','Pending'), ('confirmed','Confirmed'), ('first approved','First Approved'),('fully approved','Fully Approved'), ('rejected','Rejected')])
    student_id=fields.Many2one('res.partner',string="Student id")
    validity=fields.Integer(string="Validity")
    discount_amount=fields.Float(string="Discount amount")

