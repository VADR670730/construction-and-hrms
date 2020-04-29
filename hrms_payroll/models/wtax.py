'''
Created on 07 of December 2019

@author: Dennis
'''

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta

import logging
_logger = logging.getLogger("_name_")


class WithholdingTaxLine(models.Model):
    _name = 'withholding.tax.line'

    withholding_tax_id = fields.Many2one('withholding.tax', string="Withholding Tax", ondelete='cascade')
    wage_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('bi-monthly', 'Bi-monthly'),
        ('monthly', 'Monthly')],
        string='Wage Type', required=True)
    min_salary = fields.Float(string='Minimum Salary')
    max_salary = fields.Float(string='Maximum Salary')
    percentage = fields.Float(string='Percentage')
    additional = fields.Float(string='Prescribed Withholding Tax')

class WithholdingTax(models.Model):
    _name = 'withholding.tax'

    name = fields.Char(string="Name", default='Revised Withholding Tax Tables, version 2 (Annex "A").', required=True)
    line_ids = fields.One2many('withholding.tax.line', 'withholding_tax_id', string="Tax Range")
    valid_start = fields.Date(string="Valid From")
    valid_end = fields.Date(string="Valid End")
