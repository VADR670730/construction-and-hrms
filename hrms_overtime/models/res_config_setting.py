# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    nightdiff_hour_start = fields.Float(string="Time Start", default=22.00)
    nightdiff_hour_end = fields.Float(string="Time End", default=06.00)
    minimum_overtime_file = fields.Float(string="Minimum Overtime", default=1.00)
    overtime_rounding = fields.Float(string="Overtime Rounding")
    regular_working_hours = fields.Boolean(string="Enforce  Regular Working Hours?")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env.user.company_id.write({
            'nightdiff_hour_start': self.nightdiff_hour_start,
            'nightdiff_hour_end': self.nightdiff_hour_end,
            'minimum_overtime_file': self.minimum_overtime_file,
            'overtime_rounding': self.overtime_rounding,
            'regular_working_hours': self.regular_working_hours})

    def _get_default_nightdiff_hour_start(self):
        nightdiff = self.env.user.company_id.nightdiff_hour_start
        return nightdiff

    def _get_default_nightdiff_hour_end(self):
        nightdiff = self.env.user.company_id.nightdiff_hour_end
        return nightdiff

    def _get_default_minimum_overtime_file(self):
        minimum_overtime_file = self.env.user.company_id.minimum_overtime_file
        return minimum_overtime_file

    def _get_default_overtime_rounding(self):
        overtime_rounding = self.env.user.company_id.overtime_rounding
        return overtime_rounding

    def _get_default_regular_working_hours(self):
        regular_working_hours = self.env.user.company_id.regular_working_hours
        return regular_working_hours

    nightdiff_hour_start = fields.Float(string="Time Start", default=_get_default_nightdiff_hour_start)
    nightdiff_hour_end = fields.Float(string="Time End", default=_get_default_nightdiff_hour_end)

    minimum_overtime_file = fields.Float(string="Minimum Overtime", default=_get_default_minimum_overtime_file)
    overtime_rounding = fields.Float(string="Overtime Rounding", default=_get_default_overtime_rounding)
    regular_working_hours = fields.Boolean(string="Enforce  Regular Working Hours?", default=_get_default_regular_working_hours,
                                         help=""""While verifing as rendered, The System should as well check if the employee has rendered the regular work hours mandated.
                                         Scenario:
                                         Actual Attendance: 08:30 to 21:00 (Late for 30 mins)
                                         Filled Overtime: 17:00 to 21:00
                                         To be able to Verify as Rendered, the user should Edit the timestart to 17:30""")
