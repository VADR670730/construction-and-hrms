# -*- coding: utf-8 -*-
'''
Created on 29 January 2020
@author: Dennis
'''

from odoo import api, fields, models, _
from datetime import date, timedelta, datetime
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger("\n\n\t\t\tTesting Module 1 2 3")

class BIR1601C(models.Model):
    _name = 'bir.1601c'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin', 'document.default.approval']
    _rec_name = 'month_year'

    @api.multi
    def _get_total_nontaxable(self):
        for i in self:
            i.total_nontoxable = sum([i.mwe, i.mwe_other, i.thirtheenth_and_other_benefits, i.deminimis, i.statutory_contribution, i.other_non_taxable_amount])

    @api.multi
    def _get_total_taxable(self):
        for i in self:
            i.taxable_compensation = i.total_compensation - i.total_nontoxable
            i.net_taxable = (i.total_compensation - i.total_nontoxable) - i.taxable_compensation_non_withheld

    @api.multi
    def _get_total_remittances(self):
        for i in self:
            i.tax_withheld_remittance = sum([i.tax_withheld, i.adjustment])
            i.total_remitance_made = sum([i.tax_remitted_previously, i.other_remittance])

    @api.multi
    def _compute_tax_dues(self):
        for i in self:
            i.tax_due = i.tax_withheld_remittance - i.total_remitance_made
            i.total_penalties = sum([i.surcharge, i.interest, i.compromise])
            i.total_tax_due = sum([i.tax_due, i.total_penalties])

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env['res.company']._company_default_get('hrms_ph_statutory'), readonly=True, states={'draft': [('readonly', False)]},
                                track_visibility="always")
    month_year = fields.Char(string="Month-Year", help="MM/YYYY", required=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility="always")
    note = fields.Text(string="Notes", track_visibility="always")
    total_compensation = fields.Float(string="Total Amount of Compensation", readonly=True)
    mwe = fields.Float(string="Statutory Minimum Wage (MWEs)", help="Statutory Minimum Wage (MWEs)", readonly=True)
    mwe_other = fields.Float(string="Minimum Wage Earner", help="Holiday Pay, Overtime Pay, Night Shift, Differential Pay, Hazard Pay (Minimum Wage Earner)", readonly=True)
    thirtheenth_and_other_benefits = fields.Float(string="13th Month Pay and Other Benefits", readonly=True)
    deminimis = fields.Float(string="De Minimis Benefits", readonly=True)
    statutory_contribution = fields.Float(string="Statutory Contribution", help="SSS, GSIS, PHIC, HDMF Mandatory Contribution and Union Dues (employee's share only)", readonly=True)
    other_non_taxable_amount = fields.Float(string="Other Non-Taxable Compensation", readonly=True)
    other_non_taxable_details = fields.Char(string="Other Non-Taxable Compensation Details", readonly=True)
    total_nontoxable = fields.Float(string="Total Non-Taxable Compensation", compute="_get_total_nontaxable")
    taxable_compensation = fields.Float(string="Taxable Compensation", help="Taxable Compensation", compute="_get_total_taxable")
    taxable_compensation_non_withheld = fields.Float(string="Taxable compensation not subject to withholding tax", help="Taxable compensation not subject to withholding tax (for employees, other than MWEs, receiving P250,000 & below for the year)",
                                                     readonly=True, states={'draft': [('readonly', False)]})
    net_taxable = fields.Float(string="Net Taxable Compensation", compute="_get_total_taxable")
    tax_withheld = fields.Float(string="Total Taxes Withheld", readonly=True)
    adjustment = fields.Float(string="Adjustment", help="Add/(Less): Adjustment of Taxes Withheld from Previous Month/s (From Part IV-Schedule 1, Item 4)", readonly=True, states={'draft': [('readonly', False)]}, track_visibility="always")
    tax_withheld_remittance = fields.Float(string="Taxes Withheld for Remittance", compute="_get_total_remittances")
    tax_remitted_previously = fields.Float(string="Tax Remitted In Previously Filed", help="Less: Tax Remitted in Return Previously Filed, if this is an amended return", readonly=True, states={'draft': [('readonly', False)]})
    other_remittance = fields.Float(string="Other Remittances Amount Made", readonly=True, states={'draft': [('readonly', False)]}, track_visibility="always")
    other_remittance_detail = fields.Char(string="Other Remittances Made", readonly=True, states={'draft': [('readonly', False)]}, track_visibility="always")
    total_remitance_made = fields.Float(string="Total Tax Remittances Made", compute="_get_total_remittances")
    tax_due = fields.Float(string="Tax Still Due/(Over-remittance)", help="Tax Still Due/(Over-remittance)", compute="_compute_tax_dues")
    surcharge = fields.Float(string="Surcharge", readonly=True, states={'draft': [('readonly', False)]}, track_visibility="always")
    interest = fields.Float(string="Interest", readonly=True, states={'draft': [('readonly', False)]}, track_visibility="always")
    compromise = fields.Float(string="Compromise", readonly=True, states={'draft': [('readonly', False)]}, track_visibility="always")
    total_penalties = fields.Float(string="Total Penalties", compute="_compute_tax_dues")
    total_tax_due = fields.Float(string="Tax Amount Still Due/(Overremittance)", help="Tax Amount Still Due/(Overremittance)", compute="_compute_tax_dues")


    _sql_constraints = [
            ('month_year', 'unique (month_year, company_id)', 'Record already Exists for the given month!'),
        ]

    @api.constrains("month_year")
    def _check_month_year_format(self):
        try:
            date = datetime.strptime(self.month_year, "%m/%Y")
        except:
            raise ValidationError(_("Cutoff Month format must be in 'MM/YYYY'"))

    @api.multi
    def compute_compensation(self):
        total_compensation = basic_salary = other_salary = thirtheenth_and_other_benefits = deminimis = contributions = other_nontaxable = withholding = 0
        other_non_taxable_details = ''
        slip = self.env['hr.payslip.line'].search([
                ('slip_id.payslip_period', '=', self.month_year),
                ('slip_id.company_id', '=', self.company_id.id),
                ('salary_rule_id.bir_1601c_setting', 'not in', [False]),
                ('slip_id.state', '=', 'done')
                ])
        for i in slip:
            wage = i.slip_id.contract_id.wage
            if i.salary_rule_id.bir_1601c_setting == 'total_compensation':
                total_compensation += i.total
            elif i.salary_rule_id.bir_1601c_setting == 'basic_salary' and wage <= 20833.00:
                basic_salary += i.total
            elif i.salary_rule_id.bir_1601c_setting == 'other_salary' and wage <= 20833.00:
                other_salary += i.total
                other_non_taxable_details += 'i.name' + ', '
            elif i.salary_rule_id.bir_1601c_setting == '13th_and_other':
                thirtheenth_and_other_benefits += i.total
            elif i.salary_rule_id.bir_1601c_setting == 'deminimis':
                deminimis += i.total
            elif i.salary_rule_id.bir_1601c_setting == 'contributions':
                contributions += i.total
            elif i.salary_rule_id.bir_1601c_setting == 'other_nontaxable':
                other_nontaxable += i.total
            elif i.salary_rule_id.bir_1601c_setting == 'withholding':
                withholding += i.total
        self.write({
            'total_compensation': total_compensation,
            'mwe': basic_salary,
            'mwe_other': other_salary,
            'thirtheenth_and_other_benefits': thirtheenth_and_other_benefits,
            'deminimis': deminimis,
            'statutory_contribution': contributions,
            'other_nontaxable': other_nontaxable,
            'tax_withheld': withholding,
            })
        return True
