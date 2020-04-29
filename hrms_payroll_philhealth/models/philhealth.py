'''
Created on 27 of December 2019

@author: Dennis
'''

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta

import logging
_logger = logging.getLogger("_name_")

class HRSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    philhealth_use = fields.Boolean(string="Use for Philhealth Computation")
    philhealth_type = fields.Selection([('employee', 'Employee'), ('employer', 'Employer')], string="Philhealth Type")


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    philhealth_number = fields.Char(string="Philhealth #", size=12)

class PhilhealthContributionEmployeeSummary(models.Model):
    _name = 'philhealth.contribution.employee.summary'

    @api.depends('employer', 'employee')
    def _get_total(self):
        for i in self:
            i.total = sum([i.employer, i.employee])

    summary_id = fields.Many2one('philhealth.contribution.summary', string="Source", ondelete="cascade")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    philhealth_number = fields.Char(string="Philhealth #", related="employee_id.philhealth_number", store=True)
    employer = fields.Float(string="Employer")
    employee = fields.Float(string="Employee")
    total = fields.Float(string="Total Contribution", compute="_get_total", store=True)
    reference_number = fields.Char(string="PI Reference No.", related="summary_id.reference_number", store=True)
    applicable_date = fields.Char(string="Period Covered", related="summary_id.applicable_date", store=True)
    confirmation_number = fields.Char(string="Payment Reference", related="summary_id.confirmation_number", store=True)
    pi_status = fields.Char(string="PI Status", related="summary_id.pi_status", store=True)

class PhilhealthContributionSummary(models.Model):
    _name = 'philhealth.contribution.summary'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin', 'document.default.approval']
    _rec_name = 'reference_number'

    company_id = fields.Many2one('res.company', string="Company/Branch", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]},
                                  default=lambda self: self.env['res.company']._company_default_get('sss.contribution.summary'))
    reference_number = fields.Char(string="PI Reference No.", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    applicable_date = fields.Char(string="Period Covered", required=True, help="MM/YYYY", track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    bank = fields.Many2one('res.bank', string="Bank", track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date(string="PI Date", track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    confirmation_number = fields.Char(string="Confirmation No.", track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    transaction_time = fields.Datetime(string="Transaction Time", track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    amount = fields.Float(string="TotalAmount", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    paid_by = fields.Char(string="Paid By", track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    pi_status = fields.Char(string="PI Status")
    remarks = fields.Char(string="Remarks")
    line_ids = fields.One2many("philhealth.contribution.employee.summary", "summary_id", string="Contribution Details", readonly=True, states={'draft': [('readonly', False)]})


    @api.constrains("applicable_date")
    def _check_date_format(self):
        try:
            date = datetime.strptime(self.applicable_date, "%m/%Y")
        except:
            raise ValidationError(_("Applicable Date format must be 'MM/YYYY'"))

    @api.model
    def create(self, vals):
        res = super(PhilhealthContributionSummary, self).create(vals)
        res.get_philhealth_contributions()
        return res

    @api.multi
    def write(self, vals):
        super(PhilhealthContributionSummary, self).write(vals)
        if vals.get('applicable_date') or vals.get('applicable_date'):
            self.get_philhealth_contributions()

    @api.multi
    def get_philhealth_contributions(self):
        data = []
        for i in self.line_ids:
            i.unlink()
        payslip = self.env['hr.payslip'].search([
                            ('payslip_period', '=', self.applicable_date),
                            ('company_id', '=', self.company_id.id),
                            ('state', '=', 'done')
                        ])

        if payslip[:1]:
            employee_ids = [i.employee_id.id for i in payslip]
            for employee in employee_ids:
                slip_line = self.env['hr.payslip.line'].search([
                                    ('slip_id.employee_id', '=', employee),
                                    ('slip_id', 'in', payslip.ids),
                                    ('salary_rule_id.philhealth_use', '=', True),
                                ])
                if slip_line[:1]:
                    rec = {"employee_id": employee, 'employee': 0, 'employer': 0}
                    for line in slip_line:
                        if line.salary_rule_id.philhealth_type == 'employee':
                            rec['employee'] = rec.get('employee') + line.total
                        else:
                            rec['employer'] = rec.get('employer') + line.total
                    data.append([0, 0, rec])
        self.write({'line_ids': data})
        return True
