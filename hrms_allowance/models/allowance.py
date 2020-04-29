# -*- coding: utf-8 -*-
'''
Created on 12 January 2020
@author: Dennis
'''

from odoo import api, fields, models, _
from datetime import date, timedelta, datetime
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger("\n\n\t\t\tTesting Module 1 2 3")
#

class HRContract(models.Model):
    _inherit = 'hr.contract'

    allowance_ids = fields.One2many('hr.allowance', 'contract_id', string="Allowances")

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(HRPayslip, self).get_inputs(contracts, date_from, date_to)
        for contract in contracts:
            for allw in contract.allowance_ids:
                if allw.state == 'approved' and allw.effectivity_date <= date_to:
                    if allw.end_date:
                        if allw.end_date >= date_from:
                            input_data = {
                                'name': allw.allowance_id.name,
                                'code': allw.code,
                                'amount': allw.amount,
                                'contract_id': contract.id,
                            }
                            res += [input_data]
                    else:
                        input_data = {
                            'name': allw.allowance_id.name,
                            'code': allw.code,
                            'amount': allw.amount,
                            'contract_id': contract.id,
                        }
                        res += [input_data]
        return res

class HRAllowanceType(models.Model):
    _name = 'hr.allowance.type'

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    code = fields.Char(string="Code", required=True)
    max_amount = fields.Monetary(string="Max")
    min_amount = fields.Monetary(string="Min")
    company_id = fields.Many2one('res.company', required=True,
                                  default=lambda self: self.env['res.company']._company_default_get('hr.allowance.type'))
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency")

    @api.constrains('max_amount', 'min_amount')
    def check_amount(self):
        if self.max_amount < 0 or self.min_amount < 0:
            raise ValidationError(_('Amount must be >= zero (0)'))
        if self.min_amount > self.max_amount:
            raise ValidationError(_('Max amount should be greater than Min amount'))

class HRAllowance(models.Model):
    _name = 'hr.allowance'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'document.default.approval']

    name = fields.Char(string="Reference", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility="True")
    allowance_id = fields.Many2one('hr.allowance.type', string="Allowance", required=True, track_visibility="True", readonly=True, states={'draft': [('readonly', False)]})
    code = fields.Char(string="Code", required=True, readonly=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string="Contract", required=True, domain="[('employee_id', '=', employee_id)]", readonly=True, states={'draft': [('readonly', False)]}, track_visibility="True")
    effectivity_date = fields.Date(string="Effectivity Date", track_visibility="True", readonly=True, states={'draft': [('readonly', False)]})
    end_date = fields.Date(string="End Date", track_visibility="True", readonly=True, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', related='allowance_id.currency_id', string="Company Currency")
    amount = fields.Monetary(string="Amount Per Cutoff", track_visibility="True", readonly=True, states={'draft': [('readonly', False)]})
    description = fields.Text(string="Allowance Description", track_visibility="True", readonly=True, states={'draft': [('readonly', False)]})

    @api.constrains('end_date', 'effectivity_date')
    def check_effectivity_date(self):
        if self.effectivity_date and self.end_date:
            if self.effectivity_date >= self.end_date:
                raise ValidationError(_("Effectivity Date must be less the End Date."))

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

    @api.onchange('allowance_id')
    def onchange_allowance(self):
        if self.allowance_id:
            self.description = self.allowance_id.description
            self.code = self.allowance_id.code
            if self.allowance_id.min_amount > 0:
                self.amount = self.allowance_id.min_amount

    @api.constrains('amount', 'allowance_id')
    def _check_amount_input(self):
        if self.amount < self.allowance_id.min_amount:
            raise ValidationError(_('Amount Per Cutoff should be greater than %s'%(self.allowance_id.min_amount)))
        if self.allowance_id.max_amount > 0 and self.amount > self.allowance_id.max_amount:
            raise ValidationError(_('Amount should not be greater than %s'%(self.allowance_id.max_amount)))


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
        self.name =  self.env['ir.sequence'].next_by_code('hr.allowance')
        return super(HRAllowance, self).submit_request()


    @api.multi
    def approve_request(self):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'effectivity.date.wizard',
            'target': 'new',
            'context': {'current_id': self.id}

        }
