# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import re
class ResPartner(models.Model):
    _inherit = 'res.partner'
    reference_id = fields.Char(string='Reference ID')

# alters the display name of the res.partner
    @api.depends_context('flag')
    def _compute_display_name(self):
        if self.env.context.get('flag'):
            for record in self:
                record.display_name = record.reference_id or record.name
        else:
            return super()._compute_display_name()


    @api.constrains('reference_id')
    def check_reference_id(self):
        pattern = '^(?=(?:.*[a-zA-Z]){3})(?=(?:.*\d){3})(?=(?:.*[^a-zA-Z0-9]){2})'
        for record in self:
            if record.reference_id:
               if not re.match(pattern,record.reference_id):
                   raise UserError('the reference id should contains 3 alphabets, 3 numbers and 2 special characters.')


