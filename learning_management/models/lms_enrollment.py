# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
from odoo import Command
from odoo.orm.decorators import readonly

class LmsEnrollment(models.Model):
    _name = 'lms.enrollment'
    _description = 'Enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    course_id = fields.Many2one('product.product', string='Course id', domain=[('categ_id', '=', 'Education')],required=True, copy=False)
    name = fields.Char(string='Enrollment name', default=lambda self: ('New'), copy=False)
    refference_id = fields.Many2one('res.partner', string='Reference id', copy=False,
                                    domain=[('is_student', '!=', False)], tracking=True)
    student_id = fields.Char(related='refference_id.name', string='Student ID', context={'show_address': 1})
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    due_date = fields.Date(string='Due date', default=lambda self: fields.Date.today() + timedelta(days=15))
    course_fee = fields.Float(string='Course Fee', related='course_id.list_price', tracking=True)
    is_lead = fields.Boolean(string='Is Lead', help="Is Lead", copy=False, tracking=True)
    description = fields.Text(string='Description')
    terms_and_conditions = fields.Html()
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('done', 'Done'), ('cancel', 'Cancel')],
                             string='State', default='draft')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    dob = fields.Date(string='Date of Birth', related="refference_id.DOB", default=fields.Date.today())
    # age=fields.Integer(string='Age', default=0, compute='compute_age')
    batch_id = fields.Many2one('lms.batch', string='Batch')
    image = fields.Image(string='Image')
    scholarship_ids = fields.One2many('lms.scholarship', 'enrollment_id', string='Scholarship ID')
    all_scholarships = fields.Many2many('lms.scholarship', string='Scholarships', compute='compute_all_scholarships')
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True, copy=False, tracking=True)
    payment_status=fields.Selection([('not_applicable','Not Applicable'),('not_invoiced','Not Invoiced'),('invoice_draft','Invoice Draft'),
                                            ('not_paid','Unpaid'),('partial','partially paid'),('in_payment','In Payment'),('paid','Paid')],
                                           string='Payment Status', compute='compute_payment_status', tracking=True)

    # name sequence generation
    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if val.get('name', 'New') == "New":
                val['name'] = self.env['ir.sequence'].next_by_code('lms.enrollmenttt')
        return super(LmsEnrollment, self).create(vals)

    # function to display the payment status in enrollment form
    @api.depends('state','invoice_id','invoice_id.state','invoice_id.payment_state')
    def compute_payment_status(self):
        for record in self:
            if not record.invoice_id:
                record.payment_status = 'not_invoiced'
            elif record.invoice_id.state=='draft':
                record.payment_status = 'invoice_draft'
            else:
                record.payment_status = (record.invoice_id.payment_state or 'not_paid')

    # auto generating invoices due date
    @api.model
    def cron_generate_due_invoices(self):
        today = fields.Date.today()
        discount_product = self.env.ref('learning_management.lms_scholarship')
        enrollments = self.search([('state', '=', 'confirm'), ('due_date', '<', today), ('invoice_id', '=', False)])
        for record in enrollments:
            if not record.course_id:
                continue
            course_fee = record.course_fee
            approved_scholarships = record.scholarship_ids.filtered(
                lambda scholarship: scholarship.state in ['fully approved'])
            total_discount = sum(approved_scholarships.mapped('discount_amount'))
            if total_discount > course_fee:
                continue
            invoice_lines=[Command.create({'product_id': record.course_id.id,
                                                     'name': record.course_id.name,
                                                     'price_unit': course_fee,
                                                     'quantity': 1,
                                                     })]
            if total_discount > 0:
                invoice_lines.append(Command.create({'product_id': discount_product.id,
                                 'name': 'Scholarship Discount',
                                 'price_unit': -total_discount,
                                 'quantity': 1,
                                 }))
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': record.refference_id.id,
                'invoice_date': today,
                'invoice_line_ids': invoice_lines,
                'lms_enrollment_id': record.id
            })
            record.invoice_id = invoice.id


    @api.constrains('course_fee')
    def course_fee_validation(self):
        for record in self:
            if record.course_fee == 0:
                raise ValidationError('The course fees cannot be zero')

    @api.constrains('date')
    def date_validation(self):
        for record in self:
            if record.date < fields.Date.today():
                raise ValidationError('The Date cannot be in the past')

    # same student and course duplication validation
    @api.constrains('student_id', 'course_id')
    def student_duplication_validation(self):
        for record in self:
            duplicate = self.search(['&', ('student_id', '=', record.student_id), ('course_id', '=', record.course_id),
                                     ('id', '!=', record.id)])
            if duplicate:
                raise UserError('The student id and course id cannot be the same')

    # to checks the batch max capacity
    @api.constrains('batch_id')
    def check_batch_ids_capacity(self):
        for record in self:
            if len(record.batch_id.enrollment_ids) > record.batch_id.capacity:
                raise UserError('The total capacity is Full for this batch!')

    # to check course is same in batch and enrollment
    @api.constrains('batch_id', 'course_id')
    def check_course_in_batch_and_enrollments(self):
        for record in self:
            if record.batch_id:
                if record.course_id != record.batch_id.course_id:
                    raise UserError('The course and batch id could be the same')

    # modifying the display of scholarship records about state
    @api.onchange('scholarship_ids', 'scholarship_ids.state')
    def compute_all_scholarships(self):
        for record in self:
            record.all_scholarships = record.scholarship_ids.filtered(
                lambda scholarship: scholarship.state not in ['rejected', 'pending'])

    def confirm_button(self):
        for record in self:
            record.state = 'confirm'
            activity = self.env['mail.activity'].create({
                                                       })

    def cancel_button(self):
        for record in self:
            record.state = 'cancel'

    # mail send on done button action
    def done_button(self):
        template = self.env.ref('learning_management.mail_template_enrollment_done')
        for record in self:
            if not record.refference_id.email:
                raise UserError('The email address cannot be empty')
            record.write({'state': 'done'})
            template.send_mail(record.id, force_send=True)

    # invoices smart button in enrollment view
    def enrollment_invoice_smart_button(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'invoices button',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.invoice_id.ids)]
        }

    # @api.depends('dob', 'age')
    # def compute_age(self):
    #     for record in self:
    #         if record.dob:
    #             record.age=fields.Date.today().year-record.dob.year
    #             if fields.Date.today().month < record.dob.month:
    #                 record.age=record.age-1
    #             if record.age < 18:
    #                 raise UserError('The age should be greater than 18')

# extension inheritance to account.move
class AccountMove(models.Model):
    _inherit = 'account.move'

    lms_enrollment_id = fields.Many2one('lms.enrollment',string='LMS Enrollment', readonly=True, copy=False, index=True)

#   overriding the action.post method to send the invoice pdf as mail
    def action_post(self):
        draft_invoices=self.filtered(lambda move: move.state == 'draft' and move.move_type == 'out_invoice')
        result=super().action_post()
        template=self.env.ref('learning_management.mail_template_lms_invoice', raise_if_not_found=False)
        if template:
            for invoice in draft_invoices:
                if invoice.state=='posted' and invoice.partner_id.email:
                    template.send_mail(invoice.id, force_send=True)
                    return result


