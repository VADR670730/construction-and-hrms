# -*- coding: utf-8 -*-
'''
Created on 13 January 2020
@author: Dennis
'''

from odoo import api, fields, models, _
from datetime import date, timedelta, datetime
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger("\n\n\t\t\tTesting Module 1 2 3")

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    final_payment_id = fields.Many2one('hr.final.payment', string="Final Payment", readonly=True)

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(HRPayslip, self).get_inputs(contracts, date_from, date_to)
        if self.final_payment_id:
            for contract in contracts:
                input_data = {
                    'name': "%s Pay"%((self.final_payment_id.type_of_separation).title()),
                    'code': "SEPARATION",
                    'amount': self.final_payment_id.separation_amount,
                    'contract_id': contract.id,
                }
                res += [input_data]
                if self.final_payment_id.other_sum_allowance > 0:
                    input_data = {
                        'name': "Other Sum of Benefits",
                        'code': "SUMALW",
                        'amount': self.final_payment_id.other_sum_allowance,
                        'contract_id': contract.id,
                    }
                    res += [input_data]
                if self.final_payment_id.other_sum_deduction > 0:
                    input_data = {
                        'name': "Other Sum of Deductions",
                        'code': "SUMDED",
                        'amount': self.final_payment_id.other_sum_deduction,
                        'contract_id': contract.id,
                    }
                    res += [input_data]
        return res


class HRFinalPayment(models.Model):
    _name = 'hr.final.payment'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'document.default.approval']
    _rec_name = 'employee_id'

    @api.multi
    @api.depends('start_date', 'end_date')
    def _get_total_years(self):
        for i in self:
            if i.start_date and i.end_date:
                year = (i.end_date - i.start_date).days / 365.25
                i.total_year = year
                i.rounded_year = round(year) > 0 and round(year) or 1

    @api.depends('employee_id', 'total_year', 'type_of_separation', 'compute_separation_pay')
    def _compute_separetion(self):
        for i in self:
            i.separation_amount = 0
            if i.contract_id and i.compute_separation_pay:
                year_days = float(i.contract_id.resource_calendar_id.year_days)
                monthly_wage = i.contract_id.wage
                daily = (monthly_wage * 12) / year_days
                monthly_wage = i.contract_id.wage
                year = i.total_year
                if not i.type_of_separation in ['retirement']:
                    if (round(year) * (monthly_wage / 2)) > monthly_wage:
                        i.separation_amount = round(year) * (monthly_wage / 2)
                    else: i.separation_amount = monthly_wage
                else:
                    i.separation_amount = daily * 22.5 * round(year)

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    company_id = fields.Many2one('res.company', string="Company", store=True, related="employee_id.company_id")
    contract_id = fields.Many2one('hr.contract', string="Contract", store=True, related="employee_id.contract_id")
    job_id = fields.Many2one('hr.job', string="Job Position", store=True, related="employee_id.job_id")
    job_title = fields.Char(string="Title", store=True, related="employee_id.job_title")
    department_id = fields.Many2one('hr.department', string="Department", store=True, related="employee_id.department_id")
    type_of_separation = fields.Selection([
                            ('dismisal', 'Dismisal'),
                            ('resignation', 'Resignation'),
                            ('retirement', 'Retirement'),
                            ('layoff', 'Layoff'),
                            ('retrenchment', 'Retrenchment')
                        ], string="Type of Separation", required=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    type_of_retirement = fields.Selection([('voluntary', 'Voluntary'), ('involuntary', 'Involuntary')], string="Retirement Type", readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)

    start_date = fields.Date(string="Date Start", required=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    end_date = fields.Date(string="Date End", required=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    total_year = fields.Float(string="Year", compute="_get_total_years", store=True)
    rounded_year = fields.Integer(string="Year/s", compute="_get_total_years", store=True)

    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency")
    compute_separation_pay = fields.Boolean(string="Compute Separation Pay", default=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    separation_amount = fields.Monetary(string="Amount", compute="_compute_separetion", store=True, track_visibility=True)
    other_sum_deduction = fields.Monetary(string="Other Sum of Deduction", readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    other_sum_allowance = fields.Monetary(string="Other Sum of Benefits", readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    notes = fields.Text(string="Note/Remark", track_visibility=True)

    payslip_id = fields.Many2one('hr.payslip', string="On-hold Payslip", domain="[('for_final_payment', '=', True), ('employee_id', '=', employee_id)]")
    prev_total = fields.Monetary(string="On-hold Amount", compute="_get_amount")
    current_total_amount = fields.Monetary(string="Current Amount", compute="_get_amount")
    total = fields.Monetary(string="Final Payment Amount", compute="_get_amount")

    @api.multi
    def _get_amount(self):
        for i in self:
            prev_total = i.payslip_id and sum(line.total if line.salary_rule_id.net_salary else 0 for line in i.payslip_id.line_ids) or 0
            current_total_amount = self.env['hr.payslip.line'].search([('slip_id.final_payment_id', '=', i.id), ('salary_rule_id.net_salary', '=', True)])
            i.prev_total = prev_total
            i.current_total_amount = current_total_amount[:1] and current_total_amount[:1].total or 0
            i.total = sum([prev_total, current_total_amount[:1] and current_total_amount[:1].total or 0])

    @api.multi
    def approve_request(self):
        res = super(HRFinalPayment, self).approve_request()
        self.settle_all_nonstatutory_loans()
        return res

    @api.onchange('type_of_separation')
    def _onchange_separation_type(self):
        if not self.type_of_separation in ['retirement']:
            self.type_of_resignation = None

    @api.multi
    def settle_all_nonstatutory_loans(self):
        loan = self.env['hr.deduction'].search([
            ('contract_id', '=', self.contract_id.id),
            ('state', '=', 'approved'),
            ('loan_state', 'not in', ['paid']),
            ('deduction_type', '=', 'non-statutory')])
        for i in loan:
            i.write({'settle_at_once': True})
