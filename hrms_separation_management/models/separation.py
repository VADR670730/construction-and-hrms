from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class InheritEmployeeAddExit(models.Model):
    _inherit = 'hr.employee'

    on_hold = fields.Boolean('On Hold')
    date_started = fields.Date('Date Started')
    date_exited = fields.Date('Exit Date')
    years_of_service = fields.Char('Year(s) of Service',
                                   compute="_get_years_of_service")
    status = fields.Selection([
        ('Active', 'Active'),
        ('Resigned', 'Resigned'),
        ('Retired', 'Retired'),
        ('Terminated', 'Terminated')
    ], default='Active', string="Status")
    exit_reason = fields.Text('Exit Reason')
    separation_id = fields.Many2one('hr.separation', 'Separation File')

    @api.depends('date_started', 'date_exited')
    def _get_years_of_service(self):
        for rec in self:
            if rec.date_started:
                years_services = str(int((date.today()
                                          - rec.date_started).days
                                         / 365)) + " Year(s)"
                month = int((date.today()
                             - rec.date_started).days * 0.0328767)
                if month > 12:
                    month_services = str(month % 12) + " Month(s)"
                else:
                    month_services = str(month) + " Month(s)"
                rec.years_of_service = years_services + " , " + month_services


class HRMSSeparation(models.Model):
    _name = "hr.separation"
    _description = "Separation Management"
    _inherit = ["mail.thread", "mail.activity.mixin", "resource.mixin"]

    name = fields.Many2one('hr.employee', "Employee Name", required=True, store=True)
    department_id = fields.Many2one('hr.department', "Department", related="name.department_id")
    job_id = fields.Many2one('hr.job', "Job Position", related="name.job_id", store=True)
    parent_id = fields.Many2one('hr.employee', "Manager", related="name.parent_id", store=True)
    separation_type = fields.Selection([
        ('resignation', 'Resignation'),
        ('terminated_company', 'Termination(Company Initiated)'),
        ('terminated_infraction', 'Termination (Infraction)'),
        ('retirement', 'Retirement')
    ], string="Separation Type", required=True, store=True)
    resignation_letter = fields.Many2one('hr.resignation.letter',
                                         "Resignation Letter")
    reason = fields.Many2one('hr.resignation.reason', "Reason", required=True, store=True)
    joined = fields.Date("Joined Date", related="name.date_started", store=True)
    relieved = fields.Date("Relieved Date", required=True, store=True)
    date_raised = fields.Date("Raised on", store=True)
    date_of_request = fields.Date("Date of Request approval", store=True)
    note = fields.Text(string="Notes")

    iterview_form = fields.Many2one('survey.survey', 'Interview Form', store=True)
    quit_claim = fields.Boolean("Quit Claims", store=True)
    cert_of_employment = fields.Boolean(string="Certificate of Employment", store=True)
    details = fields.Boolean("2316 Details", store=True)
    loan = fields.Boolean("Loan Deduction Summary Table", store=True)
    clearance = fields.Boolean("Employee Clearance", default=False)

    date_submitted = fields.Date("Date Submitted")
    submitted_by = fields.Many2one('res.users', 'Submitted By')
    date_confirm = fields.Date("Date Confirmed")
    confirm_by = fields.Many2one('res.users', 'Confirmed By')
    date_approved = fields.Date("Date Approved")
    approved_by = fields.Many2one('res.users', 'Approved By')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('for_confirmation', 'Waiting for Confirmation'),
        ('for_approval', 'Waiting for Approval'),
        ('approve', 'Approved'),
        ('claim', 'Claimed')
    ], string="Status", default="draft", readonly=True, copy=False, store=True)

    @api.onchange('resignation_letter')
    def _separation_letter(self):
        for rec in self:
            if rec.resignation_letter:
                rec.relieved = rec.resignation_letter.relieved_date
                rec.reason = rec.resignation_letter.reason.id

    @api.onchange('name')
    def _duplicate_employee_entry(self):
        if self.name:
            duplicate = self.search([('name', '=', self.name.id),
                                     ('id', '!=', self._origin.id),
                                     ('state', 'in', ('for_confirmation',
                                                      'for_approval',
                                                      'approve'))])
            if duplicate:
                return {
                    'warning': {
                        'title': "Duplicate Entry",
                        'message': """Duplicate Separation Request.
                        Please Check the other records for Reference"""
                    }
                }

    @api.constrains('name')
    def check_duplicate_true(self):
        for i in self:
            if i.name:
                duplicate = self.search([('name', '=', i.name.id),
                                         ('id', '!=', i.id),
                                         ('state', 'in', ('for_confirmation',
                                                          'for_approval',
                                                          'approve'))])
            if duplicate:
                raise UserError('''Duplicate Resignation Letter.
                                Please Check the other records for Reference''')


    @api.multi
    def generate_clearance(self):
        for rec in self:
            user_id = rec.env['res.users'].browse(rec._context.get('uid'))
            clearance = rec.env['hr.exit.clearance'].create({
                'name': rec.name.id,
                'separation_parent_id': rec.id,
            })

        return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'hr.exit.clearance',
                    'res_id': int(clearance.id),
                    'view_id': False,
                }
    @api.multi
    def employee_clearance(self):
        return {
                'name': ('Exit Clearance'),
                'domain': [('name', '=', self.name.id)],
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': False,
                'res_model': 'hr.exit.clearance',
                }
    @api.multi
    def submit(self):
        for rec in self:
            duplicate = rec.search([('name', '=', rec.name.id),
                                     ('id', '!=', rec.id),
                                     ('state', 'in', ('for_confirmation',
                                                      'for_approval',
                                                      'approve'))])
            if duplicate:
                raise UserError('''Duplicate Resignation Letter.
                                Please Check the other records for Reference''')
            else:
                rec.date_raised = date.today()
                rec.date_submitted = date.today()
                user_id = self.env['res.users'].browse(self._context.get('uid'))
                rec.submitted_by = user_id.id

        return self.write({'state': 'for_confirmation'})

    @api.multi
    def confirm(self):
        for i in self:
            i.date_confirm = date.today()
            user_id = self.env['res.users'].browse(i._context.get('uid'))
            i.confirm_by = user_id.id
        return self.write({'state': 'for_approval'})

    @api.multi
    def waiting_approve(self):
        for rec in self:
            rec.date_of_request = date.today()
            rec.date_approved = date.today()
            user_id = self.env['res.users'].browse(self._context.get('uid'))
            rec.approved_by = user_id.id
        return self.write({'state': 'approve'})

    @api.multi
    def set_claim(self):
        for i in self:
            if not i.quit_claim:
                raise UserError("Employee has no Quit Claims")
            if not i.cert_of_employment:
                raise UserError("Employee has no Certificate of Employment")
            if not i.details:
                raise UserError("Employee has no 2316 Details")
            if not i.clearance:
                raise UserError("Employee has no Exit Clearance")

            if i.separation_type == "resignation":
                i.name.status = 'Resigned'
            elif i.separation_type == "retirement":
                i.name.status = 'Retired'
            else:
                i.name.status = 'Terminated'
            i.name.date_exited = i.relieved
            i.name.exit_reason = i.note
            i.name.separation_id = i.id
            i.name.active = False

            return self.write({'state':'claim'})
