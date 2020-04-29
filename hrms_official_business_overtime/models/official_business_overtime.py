# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta, time
import time as tm

import logging
_logger = logging.getLogger("_name_")

class HROfficialBusiness(models.Model):
    _inherit = 'hr.official.business'

    overtime_id = fields.Many2one('hr.overtime', string="Overtime Reference", readonly=True, copy=False)

    @api.multi
    def get_work_schedule(self, employee, date):
        schedule = self.env['resource.calendar.attendance']
        res = {'schedule_start': False, 'schedule_end': False}
        ## IDEA: Perform if Work Shifting Module is installed
        try:
            restday_shift = self.env['shifting.schedule.restday'].search([
                                        ('shifting_id.state', '=', 'approved'),
                                        ('shifting_id.employee_schedule_id', '=', employee.contract_id.resource_calendar_id.id),
                                        ('date_switch', '=',date)
                                    ])
            if restday_shift[:1]:
                for rec in restday_shift.shifting_id.employee_ids:
                    if rec.id == employee.id:
                        return res
            schedule_shift = self.env['shifting.schedule'].search([
                    ('state', '=', 'approved'),
                    ('employee_schedule_id', '=', employee.contract_id.resource_calendar_id.id),
                    ('date_end', '>=', date),
                    ('date_start', '<=', date)
                ], limit=1)
            if schedule_shift[:1]:
                for rec in schedule_shift.employee_ids:
                    if rec.id == employee.id:
                        res['schedule_start'] = datetime.combine(date, time(int(divmod((schedule_shift.start_hour * 60), 60)[0]),int(divmod((schedule_shift.start_hour * 60), 60)[1])))
                        if schedule_shift.start_hour > schedule_shift.end_hour:
                            date += timedelta(days=1)
                        res['schedule_end'] = datetime.combine(date, time(int(divmod((schedule_shift.end_hour * 60), 60)[0]),int(divmod((schedule_shift.end_hour * 60), 60)[1])))
                        return res

        except: pass
        # _logger.info("\n\n\nI Was called.\n\n")
        sched_ids = [i.id for i in schedule.search([('calendar_id', '=', employee.contract_id.resource_calendar_id.id), ('dayofweek', '=', date.weekday())])]
        if sched_ids:
            res['schedule_start'] = datetime.combine(date, time(int(divmod((schedule.browse(min(sched_ids)).hour_from * 60), 60)[0]),int(divmod((schedule.browse(min(sched_ids)).hour_from * 60), 60)[1])))
            if schedule.browse(min(sched_ids)).hour_from > schedule.browse(max(sched_ids)).hour_to:
                date += timedelta(days=1)
            res['schedule_end'] = datetime.combine(date, time(int(divmod((schedule.browse(max(sched_ids)).hour_to * 60), 60)[0]),int(divmod((schedule.browse(max(sched_ids)).hour_to * 60), 60)[1])))
            return res

    @api.multi
    def approve_request(self):
        res = super(HROfficialBusiness, self).approve_request()
        schedule = self.get_work_schedule(self.employee_id, self.ob_date)
        # _logger.info("\n\n\nI Was called. %s\n\n"%(str(schedule.get('schedule_start'))))
        if not schedule:
            overtime = self.env['hr.overtime'].create({
                    'employee_id': self.employee_id.id,
                    'overtime_start': self.date_start,
                    'overtime_end': self.date_end,
                    'description': "Official Business that falls on the Employee Restdays schedule",
                    'ob_id': self.id,
                })
            overtime.submit_request()
            overtime.approve_request()
            self.overtime_id = overtime.id
        return res

class HROvertime(models.Model):
    _inherit = 'hr.overtime'

    ob_id = fields.Many2one("hr.official.business", string="Official Business", readonly=True, ondelete='cascade', copy=False)
