# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.orm.decorators import readonly

class LmsEnrollment(models.Model):
    _name = 'lms.enrollment'
    _description = 'Enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    course_id = fields.Many2one('product.product',string='Course id', domain=[('categ_id','=','Education')], required=True, copy=False)
    name=fields.Char(string='Enrollment name', default=lambda self:('New'), copy=False)
    refference_id=fields.Many2one('res.partner',string='Reference id',copy=False, domain=[('is_student','!=', 'Active')], tracking=True)
    student_id=fields.Char(related='refference_id.name', string='Student ID', context={'show_address':1})
    date=fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    due_date=fields.Date(string='Due date', default=lambda self: fields.Date.today()+ timedelta(days=15))
    course_fee=fields.Float(string='Course Fee', related='course_id.list_price', tracking=True)
    is_lead=fields.Boolean(string='Is Lead', help="Is Lead", copy=False, tracking=True)
    description=fields.Text(string='Description')
    terms_and_conditions=fields.Html()
    state=fields.Selection([('draft','Draft'),('confirm','Confirm'),('done','Done'),('cancel','Cancel')],string='State', default='draft')
    company_id=fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id=fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    dob=fields.Date(string='Date of Birth',related="refference_id.DOB" ,default=fields.Date.today())
    # age=fields.Integer(string='Age', default=0, compute='compute_age')
    batch_id=fields.Many2one('lms.batch', string='Batch')
    image=fields.Image(string='Image')
    scholarship_ids=fields.One2many('lms.scholarship','enrollment_id', string='Scholarship ID')
    all_scholarships=fields.Many2many('lms.scholarship',string='Scholarships', compute='compute_all_scholarships')
    invoice_id=fields.Many2one('account.move', string='Invoice', readonly=True, copy=False, tracking=True)

    # name sequence generation
    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if val.get('name','New')=="New":
                val['name']=self.env['ir.sequence'].next_by_code('lms.enrollment')
        return super(LmsEnrollment,self).create(vals)

    @api.constrains('course_fee')
    def course_fee_validation(self):
        for record in self:
                if record.course_fee==0:
                    raise ValidationError('The course fees cannot be zero')

    @api.constrains('date')
    def date_validation(self):
        for record in self:
            if record.date < fields.Date.today():
                raise ValidationError('The Date cannot be in the past')

    # same student and course duplication validation
    @api.constrains('student_id','course_id')
    def student_duplication_validation(self):
        for record in self:
            duplicate=self.search(['&',('student_id','=',record.student_id),('course_id','=',record.course_id),('id','!=',record.id)])
            if duplicate:
                raise UserError('The student id and course id cannot be the same')

    # modifying the display of scholarship records about state
    @api.onchange('scholarship_ids', 'scholarship_ids.state')
    def compute_all_scholarships(self):
        for record in self:
            record.all_scholarships = record.scholarship_ids.filtered(lambda scholarship: scholarship.state not in ['rejected', 'pending'])

    def confirm_button(self):
        for record in self:
            record.state='confirm'
    def cancel_button(self):
        for record in self:
            record.state='cancel'
    def done_button(self):
        for record in self:
            record.state='done'

    # auto generating invoices due date
    @api.model
    def _cron_generate_due_invoices(self):
        today=fields.Date.today()
        enrollments=self.search([('state','=','confirm'),('due_date','<',today),('invoice_id','=',False)])
        for record in enrollments:
            if not record.refference_id:
                continue
            course_fee=record.course_fee
            if course_fee<=0:
                continue
            approved_scholarships=record.scholarship_ids.filtered(lambda scholarship: scholarship.state in ['fully approved'])
            total_discount=sum(approved_scholarships.mapped('discount_amount'))
            if total_discount>course_fee:
                continue
            invoice_lines=[
                (0,0,{
                    'product_id':record.course_id.id,
                    'name':record.course_id.display_name,
                    'quantity':1,
                    'price_unit': course_fee
                })]
            if total_discount>0:
                invoice_lines.append((0,0,{
                    'product_id':record.course_id.id,
                    'name':'scholarship discount',
                    'quantity':1,
                    'price_unit': -total_discount
                }))
            invoice=self.env['account.move'].create({
                'move_type':'out_invoice',
                'partner_id':record.refference_id.id,
                'invoice_date':today,
                'invoice_line_ids':invoice_lines,
            })
        record.invoice_id=invoice.id

    # @api.depends('dob', 'age')
    # def compute_age(self):
    #     for record in self:
    #         if record.dob:
    #             record.age=fields.Date.today().year-record.dob.year
    #             if fields.Date.today().month < record.dob.month:
    #                 record.age=record.age-1
    #             if record.age < 18:
    #                 raise UserError('The age should be greater than 18')


