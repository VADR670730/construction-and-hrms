# coding: utf-8
from odoo import models, fields, api
from datetime import date
from logging import getLogger


def log(*to_output):
    getLogger().info("\n\n\n{0}\n\n".format(to_output))


class HealthCondition(models.Model):
    _name = 'health.condition'

    employee_id = fields.Many2one('hr.employee')

    health_condition = fields.Char()
    doctor_name = fields.Char('Name of the Doctor')
    address = fields.Char()
    medications = fields.Char()
    medical_documents = fields.Binary()
    date = fields.Date()
    fit_to_work = fields.Boolean()


class Employee(models.Model):
    _inherit = 'hr.employee'

    """======================WORK INFORMATION======================"""
    mobile_phone = fields.Char(compute="_auto_populate_work_info")
    work_email = fields.Char(compute="_auto_populate_work_info")
    work_location = fields.Char(compute="_auto_populate_work_info")
    work_phone = fields.Char(compute="_auto_populate_work_info")

    """======================PRIVATE INFORMATION======================"""
    passport_validity_date = fields.Date()
    place_of_passport_issuance = fields.Char()

    marital = fields.Selection([
        ('single', 'Single'),
        ('Single Mother', 'Single Mother'),
        ('Single Father', 'Single Father'),
        ('Married', 'Married'),
        ('Divorced', 'Divorced'),
        ('Widowed', 'Widowed')
    ])

    age = fields.Integer(compute="_compute_age_years")

    """======================PRE-EMPLOYMENT INFORMATION======================"""
    sss_checkbox = fields.Boolean('SSS')
    hdmf_checkbox = fields.Boolean()
    philhealth_checkbox = fields.Boolean()
    gsis_checkbox = fields.Boolean()
    tin_checkbox = fields.Boolean()
    medical_transaction_number_checkbox = fields.Boolean()

    nbi_checkbox = fields.Boolean()
    police_checkbox = fields.Boolean()
    barangay_checkbox = fields.Boolean()

    marriage_checkbox = fields.Boolean()
    birth_checkbox = fields.Boolean()
    tor_checkbox = fields.Boolean()
    diploma_checkbox = fields.Boolean()

    sss = fields.Integer('SSS')
    hdmf = fields.Integer('HDMF')
    philhealth = fields.Integer('PhilHealth', default=None)
    gsis = fields.Integer('GSIS')
    tin = fields.Integer('TIN')
    medical_transaction_number = fields.Char()

    nbi_clearance = fields.Char('NBI')
    nbi_expiration = fields.Date()
    nbi_issued_at = fields.Char()
    nbi_date_issued = fields.Date()
    nbi_clearance_photo = fields.Binary()

    police_clearance = fields.Char('Police Clearance')
    police_expiration = fields.Date()
    police_issued_at = fields.Char()
    police_date_issued = fields.Date()
    police_clearance_photo = fields.Binary()

    barangay_clearance = fields.Char('Barangay Clearance')
    barangay_expiration = fields.Date()
    barangay_issued_at = fields.Char()
    barangay_date_issued = fields.Date()
    barangay_clearance_photo = fields.Binary()

    marriage_certificate = fields.Binary()
    birth_certificate = fields.Binary()
    transcript_of_records = fields.Binary()
    diploma = fields.Binary()

    """======================SKILLS AND TRAINING======================"""
    skill_ids = fields.One2many('hr.employee.skills', 'employee_id',
                                string="Skills")

    """======================HEALTH INFORMATION======================"""
    fit_to_work = fields.Boolean()

    height = fields.Float()
    height_uom = fields.Selection([
        ('mm', 'mm'),
        ('cm', 'cm'),
        ('inch', 'inch'),
        ('ft', 'ft')
    ])

    weight = fields.Float()
    weight_uom = fields.Selection([
        ('lbs', 'lbs'),
        ('kg', 'kg')
    ])

    blood_type = fields.Selection([
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-')
    ])
    drug_test = fields.Selection([
        ('Positive', 'Positive'),
        ('Negative', 'Negative')
    ])

    health_card_provider = fields.Char()
    id_number = fields.Char(string='ID Number')
    cap_limit = fields.Float()
    credit_usage = fields.Float()

    hmo_validity_date = fields.Date(string='HMO Validity Date')
    hmo_validity_date_end = fields.Date()
    for_renewal = fields.Boolean()
    renewal_date = fields.Date()

    health_condition_ids = fields.One2many('health.condition', 'employee_id')

    """======================EMPLOYEE MOVEMENT======================"""
    contract_history_ids = fields.One2many(
        'hr.contract', 'employee_id',
        string="Contract History",
        compute='_compute_contract_history_record'
    )

    application_id = fields.Many2one('hr.applicant')
    application_name = fields.Char(related='application_id.partner_name')

    education_ids = fields.One2many('hr.candidate.education', 'employee_id',
                                    string='Education')

    @api.multi
    def get_reference_application(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].for_xml_id('hrms_employee_201',
                                                              'open_view_reference_application')
        action['res_id'] = self.mapped('application_id').ids[0]
        return action

    @api.depends('children')
    def _compute_contract_history_record(self):
        record = self.env['hr.contract'].search([('employee_id', '=', self.id)])
        self.update({
            'contract_history_ids': [(6, 0, record.ids)],
        })

    @api.depends('birthday')
    def _compute_age_years(self):
        today = date.today()
        for rec in self:
            if rec.birthday:
                rec.age = (today.year - rec.birthday.year
                           - ((today.month, today.day) < (rec.birthday.month,
                                                          rec.birthday.day)))

    """======================WORK INFORMATION FUNCTIONS======================"""
    @api.depends('address_id')
    def _auto_populate_work_info(self):
        for rec in self:
            if rec.address_id:
                rec.mobile_phone = rec.address_id.mobile or ""
                rec.work_email = rec.address_id.email or ""
                rec.work_location = ((rec.address_id.street
                                      or "")
                                     + ", " + (rec.address_id.street2
                                               or "")
                                     + ", " + (rec.address_id.city
                                               or "")
                                     + ", " + (rec.address_id.state_id.name
                                               or "")
                                     + ", " + (rec.address_id.zip
                                               or "")
                                     + ", " + (rec.address_id.country_id.name
                                               or ""))
                rec.work_phone = rec.address_id.phone or ""
