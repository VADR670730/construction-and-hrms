'''
Created on 07 of December 2019
@author: Dennis
'''

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

import logging
_logger = logging.getLogger("_name_")

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    tin = fields.Char(string="TIN", size=12)

class HRContract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def compute_wtax(self, payslip, wtax_code, taxable_amount):
        tax_amount = 0
        slip_obj = self.env['hr.payslip.line']
        previous_contribution = 0.00
        employee = self.env['hr.employee'].browse(payslip.employee_id)
        payslip_record = self.env['hr.payslip'].search([
                        ('payslip_period', '=', payslip.payslip_period),
                        ('employee_id', '=', employee.id),
                        ('state', '=', 'done')
                        ])
        prev_wtax = sum(i.total for i in slip_obj.search([('slip_id', 'in', payslip_record.ids),('code', '=',  wtax_code)]))
        payslip_ids = payslip_record.ids
        slip_line = slip_obj.search([
                                ('slip_id', 'in', payslip_ids),
                                ('salary_rule_id.taxable_rule', 'in', ['increase', 'decrease'])
                            ])
        for i in slip_line:
            if i.salary_rule_id.taxable_rule == 'increase':
                taxable_amount += i.total
            else: taxable_amount -= i.total
        tax_range = self.env['withholding.tax.line'].search([
                                    ('wage_type', '=', 'monthly'),
                                    ('min_salary', '<=', taxable_amount),
                                    ('max_salary', '>=', taxable_amount)],
                                limit=1)
        if tax_range[:1]:
            tax_amount = tax_range[:1].additional + ((taxable_amount - tax_range[:1].min_salary) * (tax_range[:1].percentage > 0.0 and tax_range[:1].percentage / 100.00 or 0.0))
        return tax_amount - prev_wtax

    @api.multi
    def compute_13th_payout(self, payslip, codes_for_summation, payout_code):
        # code_for_summation: (list - Datatype) Salary Rule code used for Accumulated 13th month computations per payslip
        # payout_code: Salary Rule code used 13th month payout
        prev_payout = 0
        total_13th_month = 0
        if payslip.compute_thirtheenth_month:
            nov_from = datetime.strptime("%s-11-01"%(payslip.date_from.year - 1), DF)
            nov_to = datetime.strptime("%s-11-30"%(payslip.date_from.year), DF)
            employee = self.env['hr.employee'].browse(payslip.employee_id)
            payslip_record = self.env['hr.payslip'].search([
                                                ('employee_id', '=', employee.id),
                                                # ('state', '=', 'done'),
                                                ('date_to', '>=', nov_from),
                                                ('date_to', '<=', nov_to),
                                                ('paid_thirtheenth_month', '=', False)
                                            ])
            rule_code = codes_for_summation + [payout_code]
            slip_line = self.env['hr.payslip.line'].search([
                                    ('slip_id', 'in', payslip_record.ids),
                                    ('salary_rule_id.code', 'in', rule_code)
                                ])
            for i in slip_line:
                if i.salary_rule_id.code in codes_for_summation:
                    total_13th_month += i.total
                else: total_13th_month -= i.total
        return total_13th_month
