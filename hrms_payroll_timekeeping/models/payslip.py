# -*- coding: utf-8 -*-
'''
Created on 25 of January 2020
@author: Dennis
'''

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta

import logging
_logger = logging.getLogger("_name_")


class HRPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    attendance_summary_id = fields.Many2one('hr.attendance.summary', string="Attendance Summary", help="Approved Attendance Summary",
                                                readonly=True, states={'draft': [('readonly', False)]})


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    employee_attendance_summary = fields.Many2one('hr.attendance.summary.line', string="Attendance Summary",
                                                  domain="[('employee_id', '=', employee_id),('date_from', '=', date_from), ('date_to', '=', date_to)]",
                                                  readonly=True, states={'draft': [('readonly', False)]})
