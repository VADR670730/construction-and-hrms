# -*- coding: utf-8 -*-
'''
Created on 14 Feb 2020
@author: Dennis
'''
from odoo import api, fields, models, _

class HRContract(models.Model):
    _inherit = 'hr.contract'

    cutoff_template_id = fields.Many2one('payroll.cutoff.template', string="Attendance Cutoff Type")
    schedule_pay = fields.Selection([
        ('monthly', 'Monthly'),
        ('weekly', 'Weekly'),
        ('bi-monthly', 'Bi-monthly'),
    ], string='Scheduled Pay', index=True, default='monthly',
    help="Defines the frequency of the wage payment.")
    wage_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('bi-monthly', 'Bi-monthly'),
        ('weekly', 'Weekly'),
        ], string="Withholding Tax Type", default='monthly',
        related="cutoff_template_id.wtax_type")


class PayrollCutoffTemplate(models.Model):
    _name = 'payroll.cutoff.template'

    name = fields.Char(string="Title", required=True)
    cutoff_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('bi-monthly', 'Bi-monthly'),
        ('weekly', 'Weekly'),
        ], string="Attendance Cutoff Type", default='monthly')
    monthly_every_end = fields.Boolean(string="Every End-of-month", default=True)
    monthly_date = fields.Integer(string="Date", default=25)

    bimonthly_first_date = fields.Integer(string="1st Date", default=5)
    bimonthly_every_end = fields.Boolean(string="Every End-of-month", default=True)
    bimonthly_date = fields.Integer(string="2nd Date", default=25)
    day_of_week = fields.Selection([
                        ('0', 'Monday'),
                        ('1', 'Tuesday'),
                        ('2', 'Wednesday'),
                        ('3', 'Thursday'),
                        ('4', 'Friday'),
                        ('5', 'Saturday'),
                        ('6', 'Sunday'),
                    ], string="Day of Week")

    wtax_type = fields.Selection([
            ('monthly', 'Monthly'),
            ('bi-monthly', 'Bi-monthly'),
            ('weekly', 'Weekly'),
        ], string="Withholding Tax Type", default='monthly')
