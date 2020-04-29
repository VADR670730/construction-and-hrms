'''
Created on 04 of December 2019

@author: Dennis
'''

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta

import logging
_logger = logging.getLogger("_name_")

class HRSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    sss_use = fields.Boolean(string="Use for SSS Computation")
    sss_type = fields.Selection([('ee', 'EE'), ('er', 'ER'), ('ec', 'EC')], string="SSS Type")

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    sss_number = fields.Char(string="SSS #", size=10)

class SSSTableLine(models.Model):
    _name = 'sss.table.line'
    _rec_name = 'sss_id'

    @api.depends('er', 'ee', 'ec')
    def _get_total(self):
        for i in self:
            i.total = sum([i.er, i.ee, i.ec])

    sss_id = fields.Many2one('sss.table', ondelete="cascade")
    min_salary = fields.Float(string="Minimum", help="First thing to look for is your salary range on the leftmost part of the table. Determine the row of the corresponding compensation range where your monthly salary falls.")
    max_salary = fields.Float(string="Maximum", help="First thing to look for is your salary range on the leftmost part of the table. Determine the row of the corresponding compensation range where your monthly salary falls.")
    er = fields.Float(string="ER", help="ER - Stands for Employer contribution.  The contribution of your employer which is 7.37Percent of your monthly salary credit.")
    ee = fields.Float(string="EE", help="EE - Stands for Employee contribution. This is your contribution which is 3.63Percent of your monthly salary.")
    ec = fields.Float(string="EC", help="EC - Stands for Employee Compensation program. This solely shouldered by your employer")
    total = fields.Float(string="Total", compute="_get_total")


class SSSTable(models.Model):
    _name = 'sss.table'

    name = fields.Char(string="Name", default='Social Security System Contribution Table.')
    line_ids = fields.One2many('sss.table.line', 'sss_id', string="Tax Range")
    valid_start = fields.Date(string="Valid From")
    valid_end = fields.Date(string="Valid End")


class SSSContributionEmployeeSummary(models.Model):
    _name = 'sss.contribution.employee.summary'

    @api.depends('er', 'ee', 'ec')
    def _get_total(self):
        for i in self:
            i.total = sum([i.er, i.ee, i.ec])

    summary_id = fields.Many2one('sss.contribution.summary', string="Source", ondelete="cascade")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    sss_number = fields.Char(string="SSS #", related="employee_id.sss_number", store=True)
    er = fields.Float(string="ER", help="ER - Stands for Employer contribution.  The contribution of your employer which is 7.37Percent of your monthly salary credit.")
    ee = fields.Float(string="EE", help="EE - Stands for Employee contribution. This is your contribution which is 3.63Percent of your monthly salary.")
    ec = fields.Float(string="EC", help="EC - Stands for Employee Compensation program. This solely shouldered by your employer")
    total = fields.Float(string="Total Contribution", compute="_get_total", store=True)

    reference_number = fields.Char(string="ER No.", related="summary_id.reference_number", store=True)
    applicable_date = fields.Char(string="Applicaable Date", related="summary_id.applicable_date", store=True)
    payment_reference = fields.Char(string="Payment Reference", related="summary_id.payment_reference", store=True)
    trans_reference = fields.Char(string="Trans Reference no.", related="summary_id.trans_reference", store=True)



class SSSContributionSummary(models.Model):
    _name = 'sss.contribution.summary'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin', 'document.default.approval']
    _rec_name = 'reference_number'

    company_id = fields.Many2one('res.company', string="Company/Branch", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]},
                                  default=lambda self: self.env['res.company']._company_default_get('sss.contribution.summary'))
    sss_branch = fields.Char(string="SSS Branch", track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    reference_number = fields.Char(string="ER No.", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    applicable_date = fields.Char(string="Applicaable Date", required=True, help="MM/YYYY", track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    payment_reference = fields.Char(string="Payment Reference", required=True, size=14, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    trans_reference = fields.Char(string="Trans Reference no.", required=True, size=15, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    paydate = fields.Datetime(string="Pay Date", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    amount = fields.Float(string="Amount", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    cashier = fields.Char(string="Cashier", track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    line_ids = fields.One2many("sss.contribution.employee.summary", "summary_id", string="Contribution Details", readonly=True, states={'draft': [('readonly', False)]})

    @api.constrains("applicable_date")
    def _check_date_format(self):
        try:
            date = datetime.strptime(self.applicable_date, "%m/%Y")
        except:
            raise ValidationError(_("Applicable Date format must be 'MM/YYYY'"))

    @api.model
    def create(self, vals):
        res = super(SSSContributionSummary, self).create(vals)
        res.get_sss_contributions()
        return res

    @api.multi
    def write(self, vals):
        super(SSSContributionSummary, self).write(vals)
        if vals.get('applicable_date') or vals.get('applicable_date'):
            self.get_sss_contributions()

    @api.multi
    def get_sss_contributions(self):
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
                                    ('salary_rule_id.sss_use', '=', True),
                                ])
                if slip_line[:1]:
                    rec = {"employee_id": employee, 'ee': 0, 'er': 0, 'ec': 0}
                    for line in slip_line:
                        if line.salary_rule_id.sss_type == 'ee':
                            rec['ee'] = rec.get('ee') + line.total
                        elif line.salary_rule_id.sss_type == 'er':
                            rec['er'] = rec.get('er') + line.total
                        else:
                            rec['ec'] = rec.get('ec') + line.total
                    data.append([0, 0, rec])
        self.write({'line_ids': data})
        return True






class HRContract(models.Model):
    _inherit = "hr.contract"

    @api.multi
    def compute_sss(self, payslip, current_gross, contribution_type, sss_code, gross_code):
        previous_contribution = 0.00
        employee = self.env['hr.employee'].browse(payslip.employee_id)
        payslip_record = self.env['hr.payslip'].search([
                        ('employee_id.sss_number', '=', employee.sss_number),
                        ('payslip_period', '=', payslip.payslip_period),
                        ('state', '=', 'done')
                        ])
        if payslip_record[:1]:
            slip_line = self.env['hr.payslip.line'].search([
                                ('slip_id', 'in', payslip_record.ids),
                                ('code', 'in', ["SSSEE"])
                            ])
            for i in slip_line:
                if i.code == sss_code:
                    previous_contribution += i.total
                else: current_gross += i.total
        contribution = self.env['sss.table.line'].search([
                                ('sss_id.valid_start', '<=', payslip.date_from),
                                ('sss_id.valid_end', '>=', payslip.date_to),
                                ('min_salary', '<=', current_gross),
                                ('max_salary', '>=', current_gross),
                            ], limit=1)
        if not contribution[:1]: return 0
        if contribution_type == 'EE':
            return contribution.ee - previous_contribution
        elif contribution_type == 'ER':
            return contribution.er - previous_contribution
        else: return contribution.ec - previous_contribution
