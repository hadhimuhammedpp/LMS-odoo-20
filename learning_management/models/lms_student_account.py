# -*- coding: utf-8 -*-
from odoo import api, fields, models
class LMSStudentAccount(models.Model):
    _name = 'lms.student.account'
    account_id = fields.Char(string='Account ID')

    _check_account_id = models.Constraint('unique (account_id)',"The property type name must be unique!")