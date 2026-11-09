# -*- coding: utf-8 -*-
from odoo import models, fields, api
class ResPartner(models.Model):
    _inherit = 'res.partner'
    institution_id = fields.Integer(string='Institution ID')
    student_account_id = fields.Integer(string='Student Account ID')