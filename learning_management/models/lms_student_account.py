# -*- coding: utf-8 -*-
from odoo import api, fields, models
class LMSStudentAccount(models.Model):
    _name = 'lms.student.account'
    account_id = fields.Integer(string='Account ID')

    _check_account_id = models.Constraint('unique (name)',"The property type name must be unique!")