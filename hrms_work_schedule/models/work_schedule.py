# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    @api.onchange('hour_from', 'hour_to')
    def _onchange_hours(self):
        # avoid negative or after midnight
        self.hour_from = min(self.hour_from, 23.99)
        self.hour_from = max(self.hour_from, 0.0)
        self.hour_to = min(self.hour_to, 23.99)
        self.hour_to = max(self.hour_to, 0.0)

        # # avoid wrong order
        # self.hour_to = max(self.hour_to, self.hour_from)

class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    utc_offset = fields.Float(string="UTC Value", default=8.0)
    grace_period = fields.Float(string="Grace Period", default=0.25)
    late_as_halfday = fields.Float(string="Late as Halfday", default=2, help="Hours late considered as Halfday")
    break_time_hours = fields.Float(string="Breaktime", default=1.0)
    restday_workhours = fields.Float(string="Restday Work Hours", default=8.0,
                                     help="This will be the basis of computing Overtime Hours on the Restday or Holiday Works")
    year_days = fields.Selection([
        ('392.5', '392.5'),
        ('365', '365'),
        ('313', '313'),
        ('261', '261')],
        required=True,
        default='313',
        string="Days in a year",
        help="""* 392.5 -> For those who are required to work everyday including Sundays or rest days, special days and regular days;
               \n* 365 -> For those who do not work but are considered paid on the rest days, special days and regular holidays;
               \n* 313 -> For those who do not work and are not considered paid on Sundays and rest days;
               \n* 261 -> For those who do not work and are not considered paid on Saturdays and Sundays or rest days.""")

    @api.model
    def default_get(self, fields):
        res = super(ResourceCalendar, self).default_get(fields)
        res['tz'] = 'Asia/Manila'
        return res
