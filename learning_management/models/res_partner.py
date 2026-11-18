# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError
import re

class ResPartner(models.Model):
    _inherit = 'res.partner'

    reference_id = fields.Char(string='Reference ID')
    is_student=fields.Boolean(default=False, string='Is Student')
    DOB = fields.Date(string='DOB')
    enrollment_ids=fields.One2many('lms.enrollment','refference_id',string='Enrollments')
    enrollment_count=fields.Integer(string='Enrollment Count', compute='_compute_enrollment_count')


    # alters the display name of the res.partner in the enrollment Many2one drop-down field
    @api.depends_context('flag')
    def _compute_display_name(self):
        if self.env.context.get('flag'):
            for record in self:
                record.display_name = record.reference_id or record.name
        else:
            return super()._compute_display_name()

    @api.depends('enrollment_ids')
    def _compute_enrollment_count(self):
        for record in self:
            record.enrollment_count = len(record.enrollment_ids)

    def action_view_enrollments(self):
        return{
            'type': 'ir.actions.act_window',
            'name': 'Enrollments',
            'res_model': 'lms.enrollment',
            'view_mode': 'list,form',
            'domain': [('refference_id','=',self.id)],
            'context': {'default_refference_id': self.id},
        }

    # validation for reference id
    @api.constrains('reference_id')
    def check_reference_id(self):
        pattern = '^(?=(?:.*[a-zA-Z]){3})(?=(?:.*\d){3})(?=(?:.*[^a-zA-Z0-9]){2})'
        for record in self:
            if record.reference_id:
               if not re.match(pattern,record.reference_id):
                   raise ValidationError('the reference id should contains 3 alphabets, 3 numbers and 2 special characters.')


