# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta, time
import time as tm
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
import calendar
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger("_name_")

# NOTE: Second half absent will be tagged as Undertime; Only the first half will be tagged as a Halfday absent

def compute_hour_difference(date_from, date_to):
    res = 0
    if date_from and date_to:
        time_diff = (date_to - date_from).total_seconds()
        res = time_diff / 60.0 / 60.0
    return res

class HRAttendance(models.Model):
    _inherit = "hr.attendance"

    ob_id = fields.Many2one("hr.official.business", string="OB", readonly=True)

class HRUndertimeRequest(models.Model):
    _inherit = "hr.undertime.request"

    @api.depends("total_hours", "actual_ut")
    def _get_ut_difference(self):
        for i in self:
            i.time_difference = abs(i.total_hours - i.actual_ut)

    actual_ut = fields.Float(string="Actual Hours")
    time_difference = fields.Float(string="Time Difference", store=True, compute="_get_ut_difference")

class HRLeave(models.Model):
    _inherit = "hr.leave"

    # @api.onchange('date_from', 'date_to', 'employee_id', 'request_unit_half')
    # def _onchange_leave_dates(self):
    #     if self.date_from and self.date_to:
    #         regular_hours_per_day = self.employee_id.resource_calendar_id.hours_per_day
    #         date_from = date(self.date_from.year, self.date_from.month, self.date_from.day)
    #         date_to = date(self.date_to.year, self.date_to.month, self.date_to.day)
    #         self.number_of_days = ((date_to) - date_from).days # + 1
    #         if self.request_unit_half:
    #             self.number_of_days = 0.5
    #     else:
    #         self.number_of_days = 0

class HRLeaveType(models.Model):
    _inherit = "hr.leave.type"

    request_unit = fields.Selection([
        ('day', 'Day'),
        ('hour', 'Hours')
        ],
        default='day', string='Take Leaves in', required=True)

class HRAttendanceSummary(models.Model):
    _name = "hr.attendance.summary"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin', 'document.default.approval']

    name = fields.Char(string="Name", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    date_from = fields.Date(string="Date From", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    date_to = fields.Date(string="Date To", required=True, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id, track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    line_ids = fields.One2many("hr.attendance.summary.line", "attendance_summary_id", string="Employee Attendance Summary", readonly=True, states={'draft': [('readonly', False)]})
    cutoff_template_id = fields.Many2one('payroll.cutoff.template', string="Attendance Cutoff Group", required=True, readonly=True, states={'draft': [('readonly', False)]})
    cutoff_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('bi-monthly', 'Bi-monthly'),
        ('weekly', 'Weekly'),
        ], string="Attendance Cutoff Type", default='monthly', related="cutoff_template_id.cutoff_type", store=True, readonly=True, states={'draft': [('readonly', False)]})
    cutoff = fields.Selection([('1', '1st Cutoff'), ('2', '2nd Cutoff'), ('3', '3rd Cutoff'), ('4', 'Forth Cutoff')], string="Cutoff", readonly=True, states={'draft': [('readonly', False)]})
    month_year = fields.Char(string="Cutoff Month", help="MM/YYYY", required=True, readonly=True, states={'draft': [('readonly', False)]})

    @api.constrains('cutoff', 'cutoff_template_id')
    def check_cutoff(self):
        if self.cutoff in ['3', '4'] and self.cutoff_template_id.cutoff_type == 'bi-monthly':
            raise ValidationError(_('Invalid input!\nBi-monthly has only 1st and 2nd cutoff.'))

    @api.multi
    def get_dates(self, month_end_cutoff):
        month_date = datetime.strptime(self.month_year, "%m/%Y")
        try:
            prev_last_month_date = calendar.monthrange(month_date.year,month_date.month - 1)
            if prev_last_month_date[1] < month_end_cutoff:
                date_start = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month - 1, prev_last_month_date[1]), DF) + timedelta(days=1)
            else:
                date_start = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month - 1, month_end_cutoff), DF) + timedelta(days=1)
        except:
            prev_last_month_date = calendar.monthrange(month_date.year - 1, 12)
            if prev_last_month_date[1] < month_end_cutoff:
                date_start = datetime.strptime("%s-%s-%s"%(month_date.year-1, 12, prev_last_month_date[1]), DF) + timedelta(days=1)
            else:
                date_start = datetime.strptime("%s-%s-%s"%(month_date.year-1, 12, month_end_cutoff), DF) + timedelta(days=1)

        last_month_date = calendar.monthrange(month_date.year,month_date.month)
        if last_month_date[1] < month_end_cutoff:
            date_end = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month, last_month_date[1]), DF)
        else:
            date_end = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month, month_end_cutoff), DF)
        return [date_start, date_end]


    @api.onchange("cutoff_template_id", "month_year", "cutoff")
    def _onchange_month_year(self):
        if self.month_year and self.cutoff_template_id:
            self._check_month_year_format()
            self.check_cutoff()
            month_date = datetime.strptime(self.month_year, "%m/%Y")
            if self.cutoff_template_id.cutoff_type in ['monthly']:
                date_start, date_end = self.get_dates(self.cutoff_template_id.monthly_date)
            elif self.cutoff_template_id.cutoff_type == 'bi-monthly' and self.cutoff:
                date_start, date_end = self.get_dates(self.cutoff_template_id.bimonthly_date)
                if self.cutoff == '1':
                    date_end = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month, self.cutoff_template_id.bimonthly_first_date), DF)
                elif self.cutoff == '2':
                    date_start = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month, self.cutoff_template_id.bimonthly_first_date), DF) + timedelta(days=1)
            elif  self.cutoff_template_id.cutoff_type in ['weekly']:
                today = date.today()
                while today.weekday() != int(self.cutoff_template_id.day_of_week):
                    today -= timedelta(days=1)
                date_end = today
                date_start = today - timedelta(days=6)
            try:
                self.date_from  = date_start.strftime(DF)
                self.date_to = date_end.strftime(DF)
            except: pass

    @api.constrains("month_year")
    def _check_month_year_format(self):
        try:
            date = datetime.strptime(self.month_year, "%m/%Y")
        except:
            raise ValidationError(_("Cutoff Month format must be in 'MM/YYYY'"))


    @api.multi
    def compute_attendance(self):
        if len(self.line_ids) == 0: raise ValidationError(_("No employee record/s found."))
        for i in self.line_ids:
            i.compute_attendance()


class HRAttendanceComputedSummary(models.Model):
    _name = "hr.attendance.computed.summary"

    @api.depends("schedule_start", "schedule_end")
    def _get_str_wrk_schedule(self):
        for i in self:
            if i.schedule_start and i.schedule_end:
                i.schedule = "%s To %s"%(i.schedule_start.strftime("%H:%M:%S"), i.schedule_end.strftime("%H:%M:%S"))

    summary_line_id = fields.Many2one("hr.attendance.summary.line", string="Cutoff Summary", ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", string="Employee", related="summary_line_id.employee_id", store=True)
    contract_id = fields.Many2one('hr.contract', string="Contract", related="summary_line_id.contract_id", store=True)
    company_id = fields.Many2one('res.company', string="Company", related="summary_line_id.company_id", store=True)
    department_id = fields.Many2one('hr.department', string="Department", related="summary_line_id.department_id", store=True)
    job_id = fields.Many2one('hr.job', string="Position", related="summary_line_id.job_id", store=True)
    dayofweek = fields.Selection([
                    ('0', 'Monday'),
                    ('1', 'Tuesday'),
                    ('2', 'Wednesday'),
                    ('3', 'Thursday'),
                    ('4', 'Friday'),
                    ('5', 'Saturday'),
                    ('6', 'Sunday')
                ], string="Day of Week")
    date = fields.Date(string="Date")
    schedule_start = fields.Datetime(string="Schedule In")
    schedule_end = fields.Datetime(string="Schedule Out")
    schedule = fields.Char(string="Work Schedule", store=True, compute="_get_str_wrk_schedule")
    attendance = fields.Text(string="Attendance")
    offical_bussines = fields.Char(string="OB", help="Official Busness")
    night_differential = fields.Float(string="ND", help="Night Differential - Only within the regular/shift schedule")
    early_in = fields.Float(string="Early In")
    late = fields.Float(string="Late")
    undertime = fields.Float(string="Undertime")
    overtime = fields.Float(string="Overtime")
    overtime_line_ids = fields.Many2many("hr.overtime.line", "summary_computed_overtime_rel", string="Overtime")
    absent = fields.Float(string="Absent")
    regular_wrk_hour = fields.Float(string="Regular Work Hours")
    total_wrk_hour = fields.Float(string="Total Work Hours")
    holiday_ids = fields.Many2many("company.holiday", "summary_holiday_rel", string="Holidays")
    leave_ids = fields.Many2many("hr.leave", "summary_leave_rel",string="Leave")
    leave = fields.Float(string="Leave")
    unfiled_ut = fields.Boolean("Unfiled UT?", readonly=True)
    # leave_description = fields.Text(string="Leave Description")


class HRAttendanceSummaryLine(models.Model):
    _name = "hr.attendance.summary.line"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']
    _rec_name = "attendance_summary_id"


    @api.depends("total_unfiled_ut", "undertime_ids", "undertime_ids.actual_ut")
    def _get_ut_difference(self):
        for i in self:
            ut_difference = sum(abs(line.time_difference) if line.time_difference > 0.00 else 0.00 for line in i.undertime_ids)
            i.total_ut_difference = ut_difference
            i.total_ut_unauthorized = i.total_ut_difference + i.total_unfiled_ut

    @api.depends("employee_id", "contract_id", "date_from", "date_to")
    def _get_cutoff_shift_schedule(self):
        for i in self:
            shifting_ids = []
            if i.employee_id and i.contract_id and i.date_from and i.date_to:
                restday_shift = i.env['shifting.schedule.restday'].search([
                                            ('shifting_id.state', '=', 'approved'),
                                            ('shifting_id.employee_schedule_id', '=',i.contract_id.resource_calendar_id.id),
                                            ('date_switch', '>=',i.date_from),
                                            ('date_switch', '<=',i.date_to)
                                        ])
                if restday_shift[:1]:
                    for shift in restday_shift:
                        if i.employee_id.id in shift.shifting_id.employee_ids.ids:
                                shifting_ids.append(shift.shifting_id.id)
                schedule_shift1 = i.env['shifting.schedule'].search([
                        ('state', '=', 'approved'),
                        ('employee_schedule_id', '=', i.contract_id.resource_calendar_id.id),
                        ('date_start', '>=',i.date_from),
                        ('date_start', '<=',i.date_to)
                    ])
                if schedule_shift1[:1]:
                    for shift in schedule_shift1:
                        if i.employee_id.id in shift.employee_ids.ids:
                            shifting_ids.append(shift.id)
                schedule_shift2 = i.env['shifting.schedule'].search([
                        ('state', '=', 'approved'),
                        ('employee_schedule_id', '=', i.contract_id.resource_calendar_id.id),
                        ('date_end', '>=',i.date_from),
                        ('date_end', '<=',i.date_to)
                    ])
                if schedule_shift2[:1]:
                    for shift in schedule_shift2:
                        if i.employee_id.id in shift.employee_ids.ids:
                            shifting_ids.append(shift.id)
            i.shifting_schedule_ids = [(6, 0, shifting_ids)]



    attendance_summary_id = fields.Many2one("hr.attendance.summary", string="Batch Name", readonly=True, ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", string="Employee")
    date_from = fields.Date(string="Date From", required=True, track_visibility="always")
    date_to = fields.Date(string="Date To", required=True, track_visibility="always")
    contract_id = fields.Many2one('hr.contract', string="Contract",)
    company_id = fields.Many2one('res.company', string="Company", related="employee_id.company_id")
    department_id = fields.Many2one('hr.department', string="Department", related="contract_id.department_id")
    job_id = fields.Many2one('hr.job', string="Position", related="contract_id.job_id")
    overtime_ids = fields.Many2many("hr.overtime.line", 'summary_overtime_rel', string="Overtime and Holiday Works")
    summary_line_ids = fields.One2many("hr.attendance.computed.summary", 'summary_line_id', string="Attendance Summary")
    offical_bussines_ids = fields.Many2many("hr.official.business", "summary_line_ob_rel", string="Approved Official Busness Logs")
    leave_ids = fields.Many2many("hr.leave", "summary_line_leave_rel", string="Leaves")
    undertime_ids = fields.Many2many("hr.undertime.request", "summary_line_ut_rel", string="Approved and Rendered Undertime Logs")
    work_schedule_id = fields.Many2one("resource.calendar", string="Official Work Schedule", related="contract_id.resource_calendar_id")
    shifting_schedule_ids = fields.Many2many("shifting.schedule", "summary_line_shifting_schedule_rel", string="Approved Shift Schedules", store=True, compute="_get_cutoff_shift_schedule")
    total_unfiled_ut = fields.Float(string="Total Unfiled")
    total_ut_difference = fields.Float(string="Total Undertime", store=True, compute="_get_ut_difference")
    total_ut_unauthorized = fields.Float(string="Total Unauthorized", store=True, compute="_get_ut_difference")

    total_undertime = fields.Float(string="Total Undertime", store=True, compute="_get_total_ut")

    total_absent = fields.Float(string="Total Absent", readonly=True)
    total_late = fields.Float(string="Total Lates", readonly=True)
    total_late_count = fields.Float(string="Total Late Counts", readonly=True)

    total_worked_days = fields.Float(string="Total Worked Days", readonly=True)
    total_worked_hours = fields.Float(string="total Worked Hours", readonly=True)
    total_nightdifferential_hours = fields.Float(string="Total Night Differential Hours", readonly=True)
    total_unpaid_leaves = fields.Float(string="Unpaid Leaves", store=True, compute="_get_unpaid_leaves")

    @api.depends('summary_line_ids')
    def _get_total_ut(self):
        for i in self:
            i.total_undertime = sum(line.undertime for line in i.summary_line_ids)


    @api.depends('leave_ids')
    def _get_unpaid_leaves(self):
        for i in self:
            i.total_unpaid_leaves = sum(line.number_of_days if line.holiday_status_id.unpaid else 0 for line in i.leave_ids)


    @api.multi
    def generate_report(self):
        return self.env.ref('hrms_attendance_summary.attendance_summary_report').report_action(self)


    @api.multi
    def get_work_schedule(self, employee, date):
        schedule = self.env['resource.calendar.attendance']
        res = {'schedule_start': False, 'schedule_end': False}
        ## IDEA: Perform if Work Shifting Module is installed
        # try:
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

        # except: pass
        # date -= timedelta(days=1)
        sched_ids = [i.id for i in schedule.search([('calendar_id', '=', employee.contract_id.resource_calendar_id.id), ('dayofweek', '=', date.weekday())])]
        if sched_ids:
            res['schedule_start'] = datetime.combine(date, time(int(divmod((schedule.browse(min(sched_ids)).hour_from * 60), 60)[0]),int(divmod((schedule.browse(min(sched_ids)).hour_from * 60), 60)[1])))
            if schedule.browse(min(sched_ids)).hour_from > schedule.browse(max(sched_ids)).hour_to:
                date += timedelta(days=1)
            res['schedule_end'] = datetime.combine(date, time(int(divmod((schedule.browse(max(sched_ids)).hour_to * 60), 60)[0]),int(divmod((schedule.browse(max(sched_ids)).hour_to * 60), 60)[1])))
            return res


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

    @api.onchange("employee_id", "date_from", "date_to")
    def _onchange_employee(self):
        if self.employee_id and self.date_from and self.date_to:
            contract = self.get_contract(self.employee_id, self.date_from, self.date_to)
            if not contract:
                raise ValidationError(_("No valid employment contract found for %s"%(self.employee_id.name)))
            self.contract_id = contract[0]

    @api.multi
    def get_attendaces(self, employee, day_date):
        date_from = datetime.strptime('%s 00:00:00'%(day_date.strftime(DF)), DT)
        date_to = datetime.strptime('%s 23:59:59'%(day_date.strftime(DF)), DT)
        search_param = [
            ('employee_id', '=', employee.id),
            ('check_in', '>=', date_from - timedelta(hours=8)),
            ('check_in', '<=', date_to - timedelta(hours=8))
        ]
        attendance = self.env["hr.attendance"].search(search_param, order="check_in")
        return attendance

    @api.multi
    def get_late_and_undertime_computation(self, contract, attendance, work_schedule):
        # Compute Late
        grace_period = contract.resource_calendar_id.grace_period
        regular_hours_per_day = contract.resource_calendar_id.hours_per_day
        if work_schedule and regular_hours_per_day > compute_hour_difference(work_schedule.get("schedule_start"), work_schedule.get("schedule_end")):
            regular_hours_per_day = compute_hour_difference(work_schedule.get("schedule_start"), work_schedule.get("schedule_end"))
        break_time_hours = contract.resource_calendar_id.break_time_hours
        late_as_halfday = contract.resource_calendar_id.late_as_halfday
        late = compute_hour_difference(work_schedule.get("schedule_start") + timedelta(hours=grace_period), attendance[0].check_in + timedelta(hours=8))
        absent = 0.00
        if late <= 0.00:
            late = 0.00
        elif late > 0.00:
            late = compute_hour_difference(work_schedule.get("schedule_start"), attendance[0].check_in + timedelta(hours=8))

        if late_as_halfday > 0.0 and late >= late_as_halfday:
            absent = 0.5
            late = compute_hour_difference(work_schedule.get("schedule_start") + timedelta(hours=grace_period + int(regular_hours_per_day / 2.0) + break_time_hours), attendance[0].check_in + timedelta(hours=8))
            if late <= 0.00:
                late = 0.00
            elif late > 0.00:
                late = compute_hour_difference(work_schedule.get("schedule_start") + timedelta(hours=int(regular_hours_per_day / 2.0) + break_time_hours), attendance[0].check_in + timedelta(hours=8))

        # Compute Undertime
        time_start = attendance[0].check_in + timedelta(hours=8)
        if time_start < work_schedule.get("schedule_start"):
            time_start = work_schedule.get("schedule_start")
        hours_worked = compute_hour_difference(time_start, attendance[:1].check_out + timedelta(hours=8))
        undertime = regular_hours_per_day - (hours_worked - break_time_hours) - late
        if late < 0 or grace_period >= undertime:
            undertime -= grace_period
        if absent == 0.5:
            time_start = work_schedule.get("schedule_start") + timedelta(hours=int(regular_hours_per_day / 2.0) + break_time_hours)
            hours_worked = compute_hour_difference(time_start, attendance[:1].check_out + timedelta(hours=8))
            undertime = int(regular_hours_per_day / 2.0) - hours_worked - late
        if undertime <= 0.00:
            undertime = 0.00
        # Compute Early In
        early_in = compute_hour_difference(attendance[0].check_in + timedelta(hours=8), work_schedule.get("schedule_start"))
        if early_in <= 0.00:
            early_in = 0.00
        return [late, undertime, early_in, absent]

    @api.multi
    def get_night_differential_hours(self, check_in, check_out):
        nd_start = self.env.user.company_id.nightdiff_hour_start
        nd_end = self.env.user.company_id.nightdiff_hour_end
        sched_date = datetime.strptime(check_in.strftime(DF), DF)
        if check_in.hour <= nd_end:
            date = date - timedelta(days=1)
        total_hours = 0
        night_differential_start = datetime(sched_date.year, sched_date.month, sched_date.day, int(divmod((nd_start * 60), 60)[0]), int(divmod((nd_start * 60), 60)[1]))
        night_differential_end = datetime(sched_date.year, sched_date.month, sched_date.day, int(divmod((nd_end * 60), 60)[0]), int(divmod((nd_end * 60), 60)[1])) + timedelta(days=1)
        night_differential_time_start = check_in
        night_differential_time_end = check_out
        if check_in < night_differential_start:
            check_in = night_differential_start
            night_differential_time_start = night_differential_start
        if check_out > night_differential_start:

            if check_out > night_differential_end:
                total_hours = compute_hour_difference(check_in, night_differential_end)
                night_differential_time_end = night_differential_end
            else:
                total_hours = compute_hour_difference(check_in, check_out)
        return {'total_hours': total_hours > 0.0 and total_hours or 0.0, 'time_start': night_differential_time_start, 'time_end': night_differential_time_end}

    @api.multi
    def get_holiday(self, date, employee):
        holidays = self.env['company.holiday'].search([('date','=',date)])
        valid_holidays = []
        for i in holidays:
            for rec in i.company_ids:
                if employee.contract_id.company_id.id == rec.id:
                    valid_holidays.append(i.id)
        return valid_holidays

    @api.multi
    def _get_overtime_data(self, day_date, schedule, attendance, regular_wrk_hour, hours_late, hours_undertime, holidays):
        total_overtime_hours = 0.00
        overtime_ids = []
        overtime_rendered_ids = []
        overtime = self.env['hr.overtime.line'].search([
                                ('employee_id', '=', self.employee_id.id),
                                ('overtime_work_date', '=', day_date),
                                ('state', '=', 'approved')
                            ], order="start_date")
        if overtime[:1]:
            wrkschedule_end = schedule.get("schedule_end") or False
            if wrkschedule_end and sum([hours_late, hours_undertime]) > 0.0:
                wrkschedule_end = schedule.get("schedule_end") + timedelta(hours=sum([hours_late, hours_undertime]))
            for i in overtime:
                ot_start, ot_end = i.start_date + timedelta(hours=8), i.end_date + timedelta(hours=8)
                overtime_ids.append(i.id)
                if wrkschedule_end and not holidays:
                    if ot_start < wrkschedule_end and ot_start < attendance[:1].check_out + timedelta(hours=8):
                        ot_start = wrkschedule_end
                    if ot_end > attendance[:1].check_out + timedelta(hours=8):
                        ot_end = attendance[:1].check_out + timedelta(hours=8)
                    overtime_hours = compute_hour_difference(ot_start, ot_end)
                    total_overtime_hours += overtime_hours
                    if overtime_hours > 0.00:
                        overtime_rendered_ids.append(i.id)
                        i.write({'rendered_hours': overtime_hours})
                else:
                    if ot_start < attendance[0].check_in + timedelta(hours=8) and ot_start < attendance[:1].check_out + timedelta(hours=8):
                        ot_start = attendance[0].check_in + timedelta(hours=8)
                    if ot_end > attendance[:1].check_out + timedelta(hours=8):
                        ot_end = attendance[:1].check_out + timedelta(hours=8)
                    overtime_hours = compute_hour_difference(ot_start, ot_end)
                    total_overtime_hours += overtime_hours
                    if overtime_hours > 0.00:
                        overtime_rendered_ids.append(i.id)
                        i.write({'rendered_hours': overtime_hours})
        return {'total_overtime_hours': total_overtime_hours, 'overtime_ids': overtime_ids, 'overtime_rendered_ids': overtime_rendered_ids}

    @api.multi
    def compute_attendance(self):
        if self.employee_id and self.date_from and self.date_to:
            contract = self.get_contract(self.employee_id, self.date_from, self.date_to)
            if not contract:
                raise ValidationError(_("No valid employment contract found for %s"%(self.employee_id.name)))
            self.contract_id = contract[0]
            for i in self.summary_line_ids:
                i.unlink()
            attendance_summary_data = []
            ob_ids = []
            undertime_ids = []
            overtime_ids = []
            leave_ids = []
            total_unfiled_ut = 0.00
            total_absent = 0.00
            total_late = 0.00
            total_late_count = 0.00
            total_worked_days = 0.00
            total_worked_hours = 0.00
            total_nightdifferential_hours = 0.00
            regular_hours_per_day = self.contract_id.resource_calendar_id.hours_per_day
            break_time_hours = self.contract_id.resource_calendar_id.break_time_hours
            late_as_halfday = self.contract_id.resource_calendar_id.late_as_halfday
            day_date = datetime.strptime(self.date_from.strftime(DF), DF)
            for i in range((self.date_to - self.date_from).days + 1):
                rec = {
                    "dayofweek": str(day_date.weekday()),
                    "date": day_date.strftime(DF),
                }
                holidays = self.get_holiday(day_date, self.employee_id)
                leave_type = False
                rec['holiday_ids'] = holidays
                if not holidays:
                    leave_wholeday = self.env['hr.leave'].search([
                                        ('employee_id', '=', self.employee_id.id),
                                        ('request_date_from', '<=', day_date),
                                        ('request_date_to', '>=', day_date),
                                        ('request_unit_half', '=', False),
                                        ('state', '=', 'validate')
                                    ], limit=1)

                    if not leave_wholeday[:1]:
                        leave_halfday = self.env['hr.leave'].search([
                                            ('employee_id', '=', self.employee_id.id),
                                            ('request_date_from', '<=', day_date),
                                            ('request_date_to', '>=', day_date),
                                            ('request_unit_half', '=', True),
                                            ('state', '=', 'validate')
                                        ], limit=2)
                        if leave_halfday[:1]:
                            leave_halfday_count = 0
                            for leave in leave_halfday:
                                leave_halfday_count += 1
                                leave_halfday_type = leave.request_date_from_period
                            leave_type = "Halfday"
                    else: leave_type = "Wholeday"
                schedule = self.get_work_schedule(self.employee_id, day_date)
                if leave_type != "Wholeday":
                    if (leave_type == "Halfday" and leave_halfday_count == 1) or not leave_type:
                        if schedule:
                            if leave_type == "Halfday":
                                #TODO:  Fix this
                                # if leave_halfday_type == "am":
                                #     schedule['schedule_start'] = schedule.get("schedule_start") + timedelta(hours=int(regular_hours_per_day / 2.0) + break_time_hours)
                                # else: schedule['schedule_end'] = schedule.get("schedule_start") - timedelta(hours=int(regular_hours_per_day / 2.0))
                                rec['leave_ids'] = leave_halfday.ids
                                rec['leave'] = 0.5
                        offical_bussines = self.env['hr.official.business'].search([
                                    ('ob_date', '=', day_date),
                                    ('employee_id', '=', self.employee_id.id),
                                    ('state', '=', 'approved'),
                        ], limit=1)
                        if offical_bussines[:1]:
                            ob_ids.append(offical_bussines[:1].id)
                            ob_att = self.env['hr.attendance'].search([('ob_id', '=', offical_bussines.id)])
                            if not ob_att[:1]:
                                self.env['hr.attendance'].create({
                                    'employee_id': self.employee_id.id,
                                    'check_in': offical_bussines.date_start,
                                    'check_out': offical_bussines.date_end,
                                    'ob_id':  offical_bussines.id,
                                })
                        attendance = self.get_attendaces(self.employee_id, day_date)
                        if schedule:
                            operation_cutoff = self.env['hr.operation.cutoff'].search([('state', '=', 'approved')])
                            for cutoff in operation_cutoff:
                                for com in cutoff.company_ids:
                                    if com.id == self.company_id.id:
                                        if schedule.get("schedule_end"):
                                            # _logger.info("\n\nBefore Edit Schedule: %s - %s\n\n"%(schedule.get("schedule_start").strftime(DT), schedule.get("schedule_end").strftime(DT)))
                                            if cutoff.start_date <= schedule.get("schedule_end") and cutoff.end_date  + timedelta(hours=8) >= schedule.get("schedule_end"):
                                                schedule["schedule_end"] = cutoff.start_date + timedelta(hours=8)
                                                continue
                                            if cutoff.start_date + timedelta(hours=8) <= schedule.get("schedule_start") and cutoff.end_date + timedelta(hours=8) >= schedule.get("schedule_start"):
                                                schedule["schedule_start"] = cutoff.end_date + timedelta(hours=8)
                                                continue
                                            if cutoff.start_date + timedelta(hours=8) <= schedule.get("schedule_start") and cutoff.end_date + timedelta(hours=8) >= schedule.get("schedule_end"):
                                                schedule["schedule_start"] = cutoff.end_date + timedelta(hours=8)
                                                schedule = []
                                                continue
                            rec.update({
                                'schedule_start': schedule.get("schedule_start"),
                                'schedule_end': schedule.get("schedule_end")
                            })
                            if regular_hours_per_day > compute_hour_difference(schedule.get("schedule_start"), schedule.get("schedule_end")):
                                regular_hours_per_day = compute_hour_difference(schedule.get("schedule_start"), schedule.get("schedule_end"))
                        if attendance[:1]:
                            total_wrk_hour = 0.00
                            attendance_str = ''
                            for att in attendance:
                                total_wrk_hour += att.worked_hours
                                attendance_str += '%s - %s'%((att.check_in + timedelta(hours=8)).strftime(DT), (att.check_out + timedelta(hours=8)).strftime(DT))
                            rec.update({
                                'attendance': attendance_str,
                                'total_wrk_hour': total_wrk_hour,
                            })
                            if schedule:
                                total_worked_days += 1
                                # This is to make sure that the computed ND is within the Work Schedule time, other it is an NDOT
                                start_datetime = attendance[0].check_in + timedelta(hours=8)
                                if start_datetime < schedule.get("schedule_start"):
                                    start_datetime = schedule.get("schedule_start")
                                end_datetime = attendance[:1].check_out + timedelta(hours=8)
                                if end_datetime > schedule.get("schedule_end"):
                                    end_datetime = schedule.get("schedule_end")
                                hours = self.get_late_and_undertime_computation(self.contract_id, attendance, schedule)
                                # compute Halfday
                                if hours[3] == 0.5:
                                    start_datetime = schedule.get("schedule_start") + timedelta(hours=int(regular_hours_per_day / 2.0) + break_time_hours)
                                night_differential = self.get_night_differential_hours(start_datetime, end_datetime)
                                regular_wrk_hour = compute_hour_difference(start_datetime, end_datetime)
                                rec['regular_wrk_hour'] = regular_wrk_hour
                                rec.update({
                                    'late': hours[0],
                                    'undertime': hours[1],
                                    'early_in': hours[2],
                                    'absent': hours[3]
                                })
                                if hours[1] > 0.00:
                                    undertime = self.env['hr.undertime.request'].search([
                                                            ('employee_id', '=', self.employee_id.id),
                                                            ('state', '=', 'approved'),
                                                            ('ut_start_date', '=', day_date)], limit=1)
                                    if undertime[:1]:
                                        undertime.write({'actual_ut': hours[1]})
                                        undertime_ids.append(undertime.id)
                                    else:
                                        rec['unfiled_ut'] = True
                                        total_unfiled_ut += hours[1]
                                rec['night_differential'] = night_differential.get('total_hours')
                                if hours[3] == 0.5 and rec.get("leave") == 0.5:
                                    rec.update({
                                        'late': 0,
                                        'undertime': 0,
                                        'early_in': 0,
                                        'regular_wrk_hour': 0,
                                        'total_wrk_hour': 0,
                                        'attendance': ''
                                    })
                    else:
                        rec['leave_ids'] = leave_halfday.ids
                        rec['leave'] = 1.00
                else:
                    rec['leave_ids'] = leave_wholeday.ids
                    rec['leave'] = 1.00


                # if attendance[:1]:
                overtime = self._get_overtime_data(day_date, schedule, attendance, regular_hours_per_day, rec.get('late') or 0.00, rec.get('undertime') or 0.00, holidays)
                rec['overtime'] = overtime.get('total_overtime_hours')
                rec['overtime_line_ids'] = overtime.get('overtime_rendered_ids')
                overtime_ids += overtime.get('overtime_ids')
                if (rec.get('schedule_start') and rec.get('schedule_end')) and not attendance[:1] and not holidays and not rec.get("leave_ids"):
                    rec["absent"] = 1.00
                if rec.get("leave_ids"):
                    leave_ids += rec.get("leave_ids")
                total_absent += rec.get("absent") or 0.00
                total_late += rec.get("late") or 0.00
                if rec.get("late") and rec.get("late") > 0.00:
                    total_late_count += 1
                total_worked_hours += rec.get("regular_wrk_hour") or 0.00
                total_nightdifferential_hours += rec.get("night_differential") or 0.00
                day_date = day_date + timedelta(days=1)
                attendance_summary_data.append(rec)
            self.overtime_ids = overtime_ids
            self.offical_bussines_ids = ob_ids
            self.undertime_ids = undertime_ids
            self.summary_line_ids = attendance_summary_data
            self.total_unfiled_ut = total_unfiled_ut
            self.leave_ids = leave_ids
            self.total_absent = total_absent
            self.total_late = total_late
            self.total_late_count = total_late_count
            self.total_worked_days = total_worked_days
            self.total_worked_hours = total_worked_hours
            self.total_nightdifferential_hours = total_nightdifferential_hours

# TODO: to Check Overtime
#TODO: Must not allow to file leave when holidays
