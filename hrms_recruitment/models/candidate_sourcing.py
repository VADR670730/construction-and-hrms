# coding: utf-8
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date
import re
import logging
from logging import getLogger
_logger = logging.getLogger()


def log(*to_output):
    getLogger().info("\n\n\n{}\n\n".format(to_output))


class InheritContract(models.Model):
    _inherit = 'hr.contract'

    applicant_id = fields.Many2one('hr.applicant')

    @api.constrains('state')
    def restrict_running(self):
        sibling_contracts = self.env['hr.contract'].search([
            ('applicant_id', '=', self.applicant_id.id),
            ('state', '=', 'open')
        ])

        if len(sibling_contracts) > 1:
            raise UserError(
                'There can only be one Running contract per application!')


class Applicant(models.Model):
    _inherit = "hr.applicant"

    skills_ids = fields.Many2many(
        'hr.employee.skills',
        string="Skills", compute="get_skills")

    blacklisted = fields.Boolean(string="Blacklisted")

    character_reference = fields.One2many('hr.character.reference',
                                          'character_id',
                                          string="Character References")

    candidate_skills = fields.One2many('hr.employee.skills',
                                       'candidate_sourcing_id',
                                       string="Candidate Skill")

    candidate_education = fields.One2many('hr.candidate.education',
                                          'education_id',
                                          string="Candidate Education")

    candidate_work_history = fields.One2many('hr.candidate.work.history',
                                             'work_history_id',
                                             string="Candidate Work History")

    assessment_ids = fields.Many2many('hr.assessment',
                                      string="Assessments")

    requisition_id = fields.Many2one('hr.personnel.requisition',
                                     string="Job Requisition")

    contract_id = fields.Many2one('hr.contract', string="Contract",
                                  track_visibility="onchange",
                                  help="Contract linked to the applicant.")
    contract_ref_name = fields.Char(related='contract_id.name',
                                    string="Contract Reference")
    stage_id_name = fields.Char(related='stage_id.name')

    contracts_count = fields.Integer(compute='_compute_contracts_count',
                                     string='Contracts Count')

    running_contract_id = fields.Many2one('hr.contract',
                                          compute="_compute_contracts_count")

    job_qualification = fields.Text(string="Job Qualification",
                                    track_visibility='onchange',
                                    related='requisition_id.job_qualification',
                                    readonly=True)

    job_description = fields.Text(string="Job Description",
                                  track_visibility='onchange',
                                  related='requisition_id.job_description',
                                  readonly=True)

    @api.multi
    def act_hr_applicant_2_hr_contract(self):
        return {
            'name': 'Contracts',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.contract',
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'domain': [('applicant_id', '=', self.id)],
            'context': {
                'search_default_group_by_state': 1,
                'default_department_id': self.department_id.id,
                'default_job_id': self.job_id.id
            }
        }

    def _compute_contracts_count(self):
        for applicant in self:
            contracts = self.env['hr.contract'].search([
                ('applicant_id', '=', applicant.id)
            ])

            applicant.contracts_count = len(contracts)

            for contract in contracts:
                if contract.state == 'open':
                    applicant.running_contract_id = contract.id
                    return

    @api.multi
    def create_contract(self):
        self.ensure_one()

        if not self.contracts_count:
            self.env['hr.contract'].create({
                'applicant_id': self.id,
                'name': '{}'.format(self.partner_name),
                'wage': self.salary_proposed,
                'job_id': self.job_id.id,
                'department_id': self.department_id.id
            })

    @api.depends("job_id")
    def get_skills(self):
        self.update({
            'skills_ids': [(6, 0, self.job_id.skills_ids.ids)],
        })
        return True

    @api.multi
    def create_employee(self):
        employee = False
        for applicant in self:
            contact_name = False
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(['contact'])[
                    'contact']
                contact_name = applicant.partner_id.name_get()[0][1]
            else:
                new_partner_id = self.env['res.partner'].create({
                    'is_company': False,
                    'name': applicant.partner_name,
                    'email': applicant.email_from,
                    'phone': applicant.partner_phone,
                    'mobile': applicant.partner_mobile
                })
                address_id = new_partner_id.address_get(['contact'])['contact']
            if (applicant.job_id
                and (applicant.partner_name or contact_name)
                    and applicant.running_contract_id):
                applicant.job_id.write({
                    'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1
                })
                employee = self.env['hr.employee'].create({
                    'name': applicant.partner_name or contact_name,
                    'skill_ids': [(6, 0, applicant.candidate_skills.ids)],
                    'work_history_ids': [(6, 0, applicant.candidate_work_history.ids)],
                    'education_ids': [(6, 0, applicant.candidate_education.ids)],
                    'application_id': self.id,
                    'job_id': applicant.job_id.id,
                    'address_home_id': address_id,
                    'department_id': applicant.department_id.id or False,
                    'address_id': (applicant.company_id
                                   and applicant.company_id.partner_id
                                   and applicant.company_id.partner_id.id
                                   or False),
                    'work_email': (applicant.department_id
                                   and applicant.department_id.company_id
                                   and applicant.department_id.company_id.email
                                   or False),
                    'work_phone': (applicant.department_id
                                   and applicant.department_id.company_id
                                   and applicant.department_id.company_id.phone
                                   or False)
                })

                applicant.running_contract_id.write({
                    'employee_id': employee.id
                })

                applicant.write({
                    'emp_id': employee.id
                })

                applicant.job_id.message_post(
                    body=(_('New Employee %s Hired') % applicant.partner_name
                          if applicant.partner_name else applicant.name),
                    subtype="hr_recruitment.mt_job_applicant_hired")
            else:
                raise UserError(
                    _('You must define an Applied Job, Contact Name, and a Running contract for this applicant.'))

    @api.multi
    def action_get_created_contract(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].for_xml_id('hrms_recruitment',
                                                              'open_view_contract_list')
        action['res_id'] = self.mapped('contract_id').ids[0]
        return action

    @api.multi
    def action_get_assessment_tree_view(self):
        return {
            'name': _('Assessments'),
            'domain': [('applicant_name', '=', self.partner_name)],
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'hr.assessment',
        }

    @api.multi
    def archive_applicant(self):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'candidate_refuse.wizard',
            'target': 'new',
        }

    @api.multi
    def toggle_active(self):
        """ Inverse the value of the field ``active`` on the records in ``self``. """
        for record in self:
            if not self.blacklisted:
                record.active = not record.active
            else:
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'blocked.candidate.wizard',
                    'target': 'new',
                }

    @api.multi
    def reset_applicant(self):
        for record in self:
            if not self.blacklisted:
                record.active = not record.active
            else:
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'blocked.candidate.wizard',
                    'target': 'new',
                }

    @api.constrains('partner_name')
    def _duplicate_application(self):
        if self.partner_name and self.job_id:
            duplicate_archived = self.env['hr.applicant'].search([
                ('partner_name', '=', self.partner_name),
                ('active', '=', False),
                ('job_id', '=', self.job_id.id),
                ('id', '!=', self.id)
            ])
            duplicate_active = self.env['hr.applicant'].search([
                ('partner_name', '=', self.partner_name),
                ('active', '=', True),
                ('job_id', '=', self.job_id.id),
                ('id', '!=', self.id)
            ])

            if duplicate_active:
                raise ValidationError('''Application has duplicate entry!
                                      Applicant has an active application''')

            if duplicate_archived:
                raise ValidationError('''Applicant is in Archived Status!
                                      Please reopen application to manage applicant''')


class CharacterReference(models.Model):
    _name = "hr.character.reference"
    _rec_name = "character_name"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']

    character_id = fields.Many2one('hr.applicant')
    character_name = fields.Char("Name", required=True)
    character_email = fields.Char("Email", required=True)
    character_number = fields.Char("Mobile Number", required=True, size=11)
    character_credentials = fields.Char("Credentials", required=True)

    @api.constrains('character_email')
    def _check_email(self):
        emailPattern = re.compile(r'[\w.-]+@[\w-]+[.]+[\w.-]')
        if self.character_email:
            if (self.character_email
                    and not emailPattern.match(self.character_email)):
                raise ValidationError(
                    "Email is in Incorrect format \n e.g. example@company.com")


class CandidateWorkHistory(models.Model):
    _name = "hr.candidate.work.history"
    _rec_name = "work_history_id"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']

    work_history_id = fields.Many2one('hr.applicant')
    employee_id = fields.Many2one('hr.employee')
    company_name = fields.Char("Company Name", required=True)
    line_of_business = fields.Many2one('hr.candidate.work.history.company',
                                       "Line Of Business")
    position = fields.Many2one('hr.job', "Position")
    address = fields.Char("Address")
    start_date = fields.Date("Date of Start", required=True)
    end_date = fields.Date("Date of End", required=True)
    years = fields.Char("Number of years", compute="get_year_services")

    @api.depends('start_date', 'end_date')
    def get_year_services(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                years_services = str(int((rec.end_date
                                          - rec.start_date).days
                                         / 365)) + " Year(s)"
                month = int((rec.end_date
                             - rec.start_date).days * 0.0328767)
                if month > 12:
                    month_services = str(month % 12) + " Month(s)"
                else:
                    month_services = str(month) + " Month(s)"
                rec.years = years_services + " , " + month_services


class CandidateCompanyLine(models.Model):
    _name = "hr.candidate.work.history.company"
    _rec_name = "line_of_business"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']

    line_of_business = fields.Char("Line Of Business", required=True)


class CandidateEducation(models.Model):
    _name = "hr.candidate.education"
    _rec_name = "type_id"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']

    education_id = fields.Many2one('hr.applicant')
    employee_id = fields.Many2one('hr.employee')
    type_id = fields.Many2one('hr.recruitment.degree', "Level of Education",
                              required=True)
    course = fields.Many2one('hr.candidate.education.strand', "Course/Strand")
    standard = fields.Char("Standard")
    year = fields.Integer("Year")
    school_name = fields.Char("School Name")
    address = fields.Char("Address")
    vital_info = fields.Char("Other Vital Information")


class CandidateEducationCourseStrand(models.Model):
    _name = "hr.candidate.education.strand"
    _rec_name = "course_name"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']

    course_name = fields.Char("Course/Strand", required=True)


class CandidateBlacklisted(models.Model):
    _name = "hr.candidate.blacklisted"
    _rec_name = "applicant_name"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']

    applicant_name = fields.Char("Applicant Name", required=True)
    date_blocked = fields.Date("Date Blocked", required=True,
                               default=date.today())
    job_position = fields.Many2one('hr.job', "Job Position Applied",
                                   required=True)
    recruitment_stage = fields.Many2one('hr.recruitment.stage',
                                        "Recruitment Stage", required=True)
    responsible = fields.Many2one('res.users', "Responsible", required=True)
    reason = fields.Text("Reason", required=True, default="N/A")
    number_of_days = fields.Char("Number of Days", default="0")

    def reset_applicant(self):
        department = self.env['hr.applicant'].search([
            ('partner_name', '=', self.applicant_name),
            ('active', '=', False),
            ('job_id', '=', self.job_position.id)
        ])
        if department:
            department.write({
                'blacklisted': False,
                'active': True,
                'kanban_state': "normal"
            })
        self.unlink()

        return {
            'res_model': 'hr.applicant',
            'view_type': 'kanban',
            'view_mode': 'kanban',
            'view_id': False,
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
