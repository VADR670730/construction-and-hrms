# -*- coding: utf-8 -*-
'''
Created on 06 Feb 2020
@author: Dennis
'''

from odoo import api, fields, models, _

class HRSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    bir_1601c_setting = fields.Selection([
                            ('total_compensation', 'Total Amount of Compensation'),
                            ('basic_salary', 'Basic Salary'),
                            ('other_salary', 'Holiday Pay, Overtime Pay, Night Shift Differential Pay, Hazard Pay'),
                            ('13th_and_other', '13 th Month Pay and Other Benefits'),
                            ('deminimis', 'De Minimis Benefits'),
                            ('contributions', 'SSS, GSIS, PHIC, HDMF Mandatory Contributions & Union Dues (employee’s share only)'),
                            ('other_nontaxable', 'Other Non-Taxable Compensation'),
                            ('withholding', 'Withholding Tax'),
                        ], string="BIR 1601c Parameter", help="This to Identify iether taxable or not in the bir form 1601c")
