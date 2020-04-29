# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta, time
import time as tm
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
import logging
_logger = logging.getLogger("_name_")

# TODO: Check For Holidays

def compute_hour_difference(date_from, date_to):
    res = 0
    if date_from and date_to:
        time_diff = (date_to - date_from).total_seconds()
        res = time_diff / 60.0 / 60.0
    return res


class HRUndertimeRequest(models.Model):
    _name = "hr.undertime.request"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin', 'document.default.approval']


    @api.depends("ut_start")
    def _get_ut_date(self):
        for i in self:
            if i.ut_start:
                i.ut_start_date = i.ut_start.strftime(DF)


    name = fields.Char(string="Reference", default="/", copy=False)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True,
                                  states={'draft': [('readonly', False)]}, required=True, track_visibility="always")
    contract_id = fields.Many2one('hr.contract', string="Contrart",
                                  readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string="Company", related="employee_id.company_id")
    department_id = fields.Many2one('hr.department', string="Department", related="contract_id.department_id")
    job_id = fields.Many2one('hr.job', string="Position", related="contract_id.job_id")
    filing_date = fields.Date(string="Filing Date", required=True, default=fields.Date.context_today, track_visibility="always")
    # ut_date = fields.Date(string="Undertime Date", required=True, default=fields.Date.context_today)
    sched_start = fields.Datetime(string="Start")
    sched_end = fields.Datetime(string="End")
    ut_start_date = fields.Date(string="Date", store=True, compute="_get_ut_date")
    ut_start = fields.Datetime(string="UT From", required=True, track_visibility="always")
    ut_purpose = fields.Text(string="Purpose", required=True, track_visibility="always")
    total_hours = fields.Float(string="Filed Hours", track_visibility="always")


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

    @api.onchange("employee_id", "ut_start")
    def _onchange_employee(self):
        if self.employee_id and self.ut_start:
            date = datetime.strptime(self.ut_start.strftime(DF), DF)
            contract = self.get_contract(self.employee_id, date - timedelta(days=1), date + timedelta(days=1))
            if not contract:
                raise ValidationError(_("No valid employment contract found."))
            self.contract_id = contract[0]
            schedule = self.get_work_schedule(self.employee_id, date)
            if not schedule:
                raise ValidationError(_("No Valid work schedule found."))
            self.sched_start = schedule.get("schedule_start") - timedelta(hours=8)
            self.sched_end = schedule.get("schedule_end") - timedelta(hours=8)
            # _logger.info("\n\n\nData: %s \t%s"%(str(schedule), compute_hour_difference(self.ut_start, self.sched_end)))
            total_hours = compute_hour_difference(self.ut_start, self.sched_end)
            if total_hours <= 0.00:
                raise ValidationError(_("Undertime Start must be within the work schedule."))
            self.total_hours = compute_hour_difference(self.ut_start, self.sched_end)



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
        # date -= timedelta(days=1)
        sched_ids = [i.id for i in schedule.search([('calendar_id', '=', employee.contract_id.resource_calendar_id.id), ('dayofweek', '=', date.weekday())])]
        if sched_ids:
            res['schedule_start'] = datetime.combine(date, time(int(divmod((schedule.browse(min(sched_ids)).hour_from * 60), 60)[0]),int(divmod((schedule.browse(min(sched_ids)).hour_from * 60), 60)[1])))
            if schedule.browse(min(sched_ids)).hour_from > schedule.browse(max(sched_ids)).hour_to:
                date += timedelta(days=1)
            res['schedule_end'] = datetime.combine(date, time(int(divmod((schedule.browse(max(sched_ids)).hour_to * 60), 60)[0]),int(divmod((schedule.browse(max(sched_ids)).hour_to * 60), 60)[1])))
            return res

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
    def submit_request(self):
        res = super(HRUndertimeRequest, self).submit_request()
        self.write({'name': self.env['ir.sequence'].get('undertime.request')})
        self.add_follower(self.employee_id.id)
        msg_body = '''%s is requesting approval for Undertime:
        <br/>Datetime:  %s to %s
        <br/>Purpose:
        <br/><ul>
            %s
            </ul>'''%(self.employee_id.name,(self.ut_start + timedelta(hours=8)).strftime(DT) , (self.sched_end + timedelta(hours=8)).strftime(DT), self.ut_purpose)
        self.message_post(body=msg_body,subject="Official Busness - for Approval")
        return res
