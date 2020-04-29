# -*- coding: utf-8 -*-
'''
Created on 12 January 2020
@author: Dennis
'''

from odoo import api, fields, models, _
from datetime import date, timedelta, datetime
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger("\n\n\t\t\tTesting Module 1 2 3")

class HRPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    deduction_id = fields.Many2one('hr.deduction', string="Deduction Reference")

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(HRPayslip, self).get_inputs(contracts, date_from, date_to)
        for contract in contracts:
            deduction = self.env['hr.deduction'].search([('employee_id', '=', contract.employee_id.id),('state', '=', 'approved'), ('loan_state', '=', 'inprogress'), ('remaining_balance', '>', 0)])
            for rec in deduction:
                amount = rec.payable_per_cutoff
                if rec.settle_at_once: amount = rec.remaining_balance
                input_data = {
                    'name': rec.deduction_id.name,
                    'code': rec.code,
                    'amount': amount,
                    'contract_id': contract.id,
                    'deduction_id': rec.id,
                }
                res += [input_data]
        return res

    @api.multi
    def action_payslip_done(self):
        res = super(HRPayslip, self).action_payslip_done()
        if not self.for_final_payment:
            self.post_deduction_payment()
        return res

    @api.multi
    def post_deduction_payment(self):
        for i in self.input_line_ids:
            if i.deduction_id:
                data = {
                    'deduction_id': i.deduction_id.id,
                    'payslip_id': self.id,
                    'amount': i.amount,
                    'remaining_balance': i.deduction_id.remaining_balance - i.amount
                }
                rec = self.env['hr.deduction.line'].create(data)
        return True


class HRDeductionType(models.Model):
    _name = 'hr.deduction.type'

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    deduction_type = fields.Selection([('non-statutory', 'Non-statutory'),('statutory', 'Statutory')], string="Deduction Type", required=True)
    code = fields.Char(string="Code", required=True)

class HRDeductionLine(models.Model):
    _name = 'hr.deduction.line'

    deduction_id = fields.Many2one('hr.deduction', string="Deduction Reference")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip")
    date_from = fields.Date(string="Date From", related="payslip_id.date_from")
    date_to = fields.Date(string="Date To", related="payslip_id.date_to")
    currency_id = fields.Many2one('res.currency', related='payslip_id.company_id.currency_id', string="Currency")
    amount = fields.Monetary(string="Amount")
    remaining_balance = fields.Monetary(string="Remaining Balance")


class HRDeduction(models.Model):
    _name = 'hr.deduction'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'document.default.approval']

    @api.depends('date_from', 'payable_months', 'monthly_payable', 'contract_id')
    def _get_payable_per_cutoff(self):
        for i in self:
            if i.contract_id and i.date_from and i.monthly_payable > 0.0 and i.payable_months > 0.0:
                datefrom = i.date_from
                dateTo = datefrom + relativedelta(months = i.payable_months)
                d1 = (datefrom - timedelta(days=datefrom.weekday()))
                d2 = (dateTo - timedelta(days=dateTo.weekday()))
                weeks = (d2 - d1).days / 7
                if weeks <= 0.0:
                    weeks = 1
                payable_per_cutoff = i.monthly_payable
                if i.contract_id.cutoff_template_id.cutoff_type == 'weekly':
                    payable_per_cutoff = (i.monthly_payable * i.payable_months) / weeks
                elif i.contract_id.cutoff_template_id.cutoff_type == 'bi-monthly':
                    payable_per_cutoff = i.monthly_payable / 2.0
                paid_amount = 0.0
                i.number_of_week = weeks
                i.date_to = dateTo
                i.payable_per_cutoff = payable_per_cutoff
                i.total_deduction = i.monthly_payable * i.payable_months

    @api.depends('total_deduction', 'line_ids')
    def _get_remaining_balance(self):
        for i in self:
            balance_amount = i.total_deduction - sum(line.amount for line in i.line_ids)
            i.remaining_balance = balance_amount
            if balance_amount <= 0:
                i.set_paid()


    name = fields.Char(string="Reference", default='/')
    currency_id = fields.Many2one('res.currency', related='employee_id.company_id.currency_id', string="Company Currency")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    contract_id = fields.Many2one('hr.contract', string="Contract", required=True, domain="[('employee_id', '=', employee_id)]", track_visibility=True, readonly=True, states={'draft': [('readonly', False)]})
    deduction_id = fields.Many2one('hr.deduction.type', string="Deduction", required=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    deduction_type = fields.Selection([('non-statutory', 'Non-statutory'),('statutory', 'Statutory')], string="Deduction Type", related="deduction_id.deduction_type", store=True)
    code = fields.Char(string="Code", required=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    settle_at_once = fields.Boolean(string="Settle At Once", track_visibility=True)
    monthly_payable = fields.Monetary(string="Monthly Amortization", help="Amortization + Interest", required=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    payable_months = fields.Integer(string="Payable Months", required=True, default=1, readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    number_of_week = fields.Integer(string="No. of Weeks", compute='_get_payable_per_cutoff', store=True, track_visibility=True)
    date_from = fields.Date(string='Start Date', required=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    date_to = fields.Date(string='End Date', compute='_get_payable_per_cutoff', store=True, track_visibility=True)
    payable_per_cutoff = fields.Float(string="Payable per Cutoff", compute='_get_payable_per_cutoff', store=True)
    total_deduction = fields.Float(string="Total Deduction", compute='_get_payable_per_cutoff', store=True)
    description = fields.Text(string="Description", readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    loan_state = fields.Selection([('paused', 'Paused'), ('inprogress', 'In Progress'), ('paid', 'Paid')], string="Loan Status", track_visibility=True, readonly=True)
    line_ids = fields.One2many('hr.deduction.line', 'deduction_id', string="Payment History", readonly=True)
    remaining_balance = fields.Monetary(string="Remaining Balance", store=True, compute="_get_remaining_balance", track_visibility=True)


    @api.multi
    def approve_request(self):
        return self.write({
                'state': 'approved',
                'approved_by': self._uid,
                'approved_date': datetime.now(),
                'loan_state': 'inprogress',
            })

    @api.multi
    def set_inprogress(self):
        return self.write({'loan_state': 'inprogress'})

    @api.multi
    def set_paused(self):
        return self.write({'loan_state': 'paused'})

    @api.multi
    def set_paid(self):
        return self.write({'loan_state': 'paid'})


    @api.constrains('monthly_payable', 'payable_months')
    def _check_payable_input(self):
        if self.monthly_payable and self.monthly_payable <= 0.0:
            raise ValidationError(_('Monthly Amortization should be greater then Zero (0)'))
        if self.payable_months and self.payable_months <= 0.0:
            raise ValidationError(_('Payable Months should be greater then Zero (0)'))

    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|', '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids

    @api.onchange('deduction_id')
    def onchange_deduction(self):
        if self.deduction_id:
            self.description = self.deduction_id.description
            self.code = self.deduction_id.code


    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            vals = {}
            contract = self.get_contract(self.employee_id, date.today(), date.today())
            if contract: self.contract_id = contract[0]
            vals['domain'] = {
                "contract_id": [("id", "in", contract)],
            }
            return vals

    @api.multi
    def submit_request(self):
        self.name =  self.env['ir.sequence'].next_by_code('hr.deduction')
        return super(HRDeduction, self).submit_request()
