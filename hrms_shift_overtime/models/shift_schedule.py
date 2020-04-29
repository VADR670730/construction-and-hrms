# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta, time

class HROvertime(models.Model):
    _inherit = 'hr.overtime'

    # IDEA:
    # check filed date is Switched Restday. If true then, return Restday
    # otherwise,
    #     check filed date is a shifted schedule. It true the, return Shift Schedule
    # else check regular schedule

    @api.multi
    def get_date_schedule(self, employee, date):
        schedule = self.env['resource.calendar.attendance']
        res = {'schedule_start': False, 'schedule_end': False}
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

        sched_ids = [i.id for i in schedule.search([('calendar_id', '=', employee.contract_id.resource_calendar_id.id), ('dayofweek', '=', date.weekday())])]
        if sched_ids:
            res['schedule_start'] = datetime.combine(date, time(int(divmod((schedule.browse(min(sched_ids)).hour_from * 60), 60)[0]),int(divmod((schedule.browse(min(sched_ids)).hour_from * 60), 60)[1])))
            if schedule.browse(min(sched_ids)).hour_from > schedule.browse(max(sched_ids)).hour_to:
                date += timedelta(days=1)
            res['schedule_end'] = datetime.combine(date, time(int(divmod((schedule.browse(max(sched_ids)).hour_to * 60), 60)[0]),int(divmod((schedule.browse(max(sched_ids)).hour_to * 60), 60)[1])))
            return res
