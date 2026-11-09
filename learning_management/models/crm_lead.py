# -*- coding: utf-8 -*-
from odoo import api,fields,models
class CrmLead(models.Model):
    _inherit = "crm.lead"
    enrollment_id = fields.Integer(string="Enrolment ID")