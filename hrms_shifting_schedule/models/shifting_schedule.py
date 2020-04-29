# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import pytz
from datetime import date, datetime, timedelta
import time
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
import calendar
import math
import logging
_logger = logging.getLogger("_name_")

# Decimal to time format
def convert_to_time(dec_hours):
    seconds = dec_hours * 60 * 60
    return time.strftime("%H:%M:%S", time.gmtime(seconds))

class HRShiftingScheduleRestday(models.Model):
    _name = "shifting.schedule.restday"

    date_original = fields.Date(string="Original")
    date_switch = fields.Date(string="Switch To")
    shifting_rest_id = fields.Many2one("shifting.schedule", string="Reference")
    shifting_id = fields.Many2one("shifting.schedule", string="Schedule", ondelete='cascade')


class HRShiftingSchedule(models.Model):
    _name = "shifting.schedule"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin', 'document.default.approval']

    name = fields.Char(string="Title", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Datetime(string="Date Filed", track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    employee_schedule_id = fields.Many2one('resource.calendar', string="Work Schedules", required=True, readonly=True, states={'draft': [('readonly', False)]})
    date_start = fields.Date(string="Start Date", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    date_end = fields.Date(string="End Date", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    restday_ids = fields.One2many("shifting.schedule.restday", "shifting_id", string="Restday Switch", readonly=True, states={'draft': [('readonly', False)]})
    start_hour = fields.Float(string="Hour Start", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    end_hour = fields.Float(string="Hour Start", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    notes = fields.Text(string="Notes", readonly=True, states={'draft': [('readonly', False)]})
    employee_ids = fields.Many2many('hr.employee', 'shifting_employee_rel', string="Employees", track_visibility="always", required=True, readonly=True, states={'draft': [('readonly', False)]})

    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|', '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids

    @api.onchange("employee_schedule_id", "date_start", "date_end")
    def _onchange_employees(self):
        if self.employee_schedule_id and self.date_start and self.date_end:
            dayofweek = [int(i.dayofweek) for i in self.employee_schedule_id.attendance_ids]
            date, data = self.date_start, []
            self.restday_ids = [(5,)]
            for i in range((self.date_end - self.date_start).days + 1):
                if not date.weekday() in set(dayofweek):
                    data.append([0, 0, {'date_original': date}])
                date = date + timedelta(days=1)
            self.restday_ids = data

    @api.onchange("employee_schedule_id", "company_id")
    def _onchange_schedule_id(self):
        vals = {}
        if self.employee_schedule_id and self.company_id:
            self.employee_ids = [(5,)]
            employee_ids = [i.employee_id.id for i in self.env['hr.contract'].search([
                            ('resource_calendar_id', '=', self.employee_schedule_id.id),
                            ('company_id', '=', self.company_id.id)
                        ])]
            vals['domain'] = {
                "employee_ids": [("id", "in", employee_ids)],
            }
            return vals

    @api.onchange('start_hour', 'end_hour')
    def onchange_hours(self):
        if self.start_hour and self.end_hour:
            if self.start_hour >= 24.00 or self.start_hour < 0.00 or self.end_hour >= 24.00 or self.end_hour < 0.00 or self.end_hour == self.start_hour:
                raise ValidationError("Invalid hours")

    @api.onchange("employee_schedule_id", "date_end", "restday_ids", "restday_ids.date_switch", "restday_ids.date_original")
    def _onchange_field(self):
        if self.employee_schedule_id and self.date_start and self.date_end and len(self.restday_ids) > 0:
            restday_dates = []
            dayofweek = [int(i.dayofweek) for i in self.employee_schedule_id.attendance_ids]
            for i in self.restday_ids:
                if i.date_switch and i.date_original:
                    restday_dates.append(i.date_switch.strftime(DF))
                    if i.date_switch <= i.date_original or i.date_switch <= self.date_end:
                        raise ValidationError("Invalid Restdays Input.")

                    if not i.date_switch.weekday() in set(dayofweek):
                        raise ValidationError("Invalid Restdays Input.\n%s is a regular Restday schedule."%(i.date_switch.strftime(DF)))
            if len(restday_dates) != len(set(restday_dates)):
                raise ValidationError("Invalid Restdays Input. Duplicate dates is not allowed")

    @api.multi
    def check_shift_schedule(self):
        data_shift = self.search([
                        ('id', '!=', self.id),
                        ('employee_schedule_id', '=', self.employee_schedule_id.id),
                        ('state', 'not in', ['canceled']),
                        ("date_end",">=",self.date_start),
                        ("date_end","<=",self.date_end)
                    ])
        msg = ''
        if data_shift[:1]:
            msg += 'The Shift Schedule has already filed for the following employees:\n\n'
            for shift_rec in data_shift:
                for rec in shift_rec.employee_ids:
                    if rec.id in self.employee_ids.ids:
                        msg += "Employee: %s document: %s Status: %s\n"%(rec.name, shift_rec.name, (shift_rec.state).capitalize())
        #Check for Restday conflicts for Shift schedule inputs
        elif not data_shift[:1]:
            data_shift = self.env['shifting.schedule.restday'].search([
                                        ('shifting_id.id', '!=', self.id),
                                        ('shifting_id.employee_schedule_id', '=', self.employee_schedule_id.id),
                                        ('date_switch', '>=', self.date_start),
                                        ('date_switch', '<=', self.date_end)
                                    ])
            for shift_rec in data_shift:
                for rec in shift_rec.shifting_id.employee_ids:
                    if rec.id in self.employee_ids.ids:
                        msg += "Employee: %s document: %s Status: %s\n"%(rec.name, shift_rec.name, (shift_rec.state).capitalize())
        #Check for Restday conflicts for restday inputs
        elif not data_shift[:1] and len(self.restday_ids) > 0:
            for rest in self.restday_ids:
                data_shift_restday = self.env['shifting.schedule.restday'].search([
                                            ('shifting_id.id', '!=', self.id),
                                            ('shifting_id.employee_schedule_id', '=', self.employee_schedule_id.id),
                                            ('date_switch', '=', rest.date_switch)
                                        ])
                if data_shift_restday[:1]:
                    msg += 'The Shift Schedule Restdays has conflicts for the following employees:\n\n'
                    for shift_rest_rec in data_shift_restday:
                        for rec in shift_rest_rec.shifting_id.employee_ids:
                            if rec.id in self.employee_ids.ids:
                                msg += "Employee: %s document: %s Status: %s\n"%(rec.name, shift_rest_rec.shifting_id.name, (shift_rest_rec.shifting_id.state).capitalize())

        if msg != '':
            raise ValidationError("%s\nPlease solve the conflicted Schedules to proceed to the next step."%(msg))
        else:
            return True

    @api.multi
    def add_follower(self, employee_ids):
        partner_ids = []
        for employee in self.env['hr.employee'].browse(employee_ids):
            if employee.parent_id and employee.parent_id.user_id:
                partner_ids.append(employee.parent_id.user_id.partner_id.id)
            if employee.user_id:
                partner_ids.append(employee.user_id.partner_id.id)
        if partner_ids:
            self.message_subscribe(partner_ids=partner_ids)

    @api.multi
    def approve_request(self):
        self.add_follower(self.employee_ids.ids)
        res = super(HRShiftingSchedule, self).approve_request()
        employee = [i.name for i in self.employee_ids]
        employee = employee and ((str(employee).replace("'", '')).replace('[', '')).replace(']', '') or False
        restday = [(i.date_switch).strftime(DF) for i in self.restday_ids]
        restday = restday and ((str(restday).replace("'", '')).replace('[', '')).replace(']', '') or False

        msg_body = '''Approved work shift schedule for the employees:
        <br/><br/>%s
        <br/>Date:  %s to %s
        <br/>Time: %s - %s
        <br/>Assigned Restday/s: %s
        <br/>Notes: <br/><ul>%s</ul>'''%(employee, (self.date_start).strftime(DF), (self.date_end).strftime(DF),  convert_to_time(self.start_hour),  convert_to_time(self.end_hour), restday, self.notes)
        self.message_post(body=msg_body,subject="Work Shift Schedule - %s"%(self.name))
        return res

    @api.multi
    def submit_request(self):
        for i in self.restday_ids:
            if not i.date_switch:
                raise ValidationError(_("Please set a Restday Switch of %s"%(i.date_original)))
        self.check_shift_schedule()
        return super(HRShiftingSchedule, self).submit_request()
