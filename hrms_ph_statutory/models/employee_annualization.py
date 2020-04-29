# -*- coding: utf-8 -*-
'''
Created on 7th of Feb 2020
@author: Dennis
'''

from odoo import api, fields, models, _
from datetime import date, timedelta, datetime
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger("\n\n\t\t\tTesting Module 1 2 3")


class EmployeeAnnualization(models.Model):
    _name = 'employee.annualization'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin', 'document.default.approval']
    _rec_name = 'year'

    @api.constrains("year")
    def _check_month_year_format(self):
        try:
            date = datetime.strptime(self.year, "%Y")
        except:
            raise ValidationError(_("Cutoff Month format must be in 'YYYY'"))

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env['res.company']._company_default_get('hrms_ph_statutory'),
                                track_visibility="always")
    note = fields.Text(string="Notes", track_visibility="always")
    year = fields.Char(string="Month-Year", help="YYYY", required=True, track_visibility="always")


    @api.multi
    def get_71xls(self):
        return self.env.ref('hrms_ph_statutory.hrms_71_xlsx').report_action(self)

    @api.multi
    def get_73xls(self):
        return self.env.ref('hrms_ph_statutory.hrms_73_xlsx').report_action(self)

    @api.multi
    def get_74xls(self):
        return self.env.ref('hrms_ph_statutory.hrms_74_xlsx').report_action(self)

    @api.multi
    def get_75xls(self):
        return self.env.ref('hrms_ph_statutory.hrms_75_xlsx').report_action(self)
