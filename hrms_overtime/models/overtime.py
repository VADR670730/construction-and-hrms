# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import pytz
from datetime import date, datetime, timedelta, time
import time as tm
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
    return tm.strftime("%H:%M:%S", tm.gmtime(seconds))

def compute_hour_difference(date_from, date_to):
    res = 0
    if date_from and date_to:
        time_diff = (date_to - date_from).total_seconds()
        res = time_diff / 60.0 / 60.0
    return res

class HROvertimeLine(models.Model):
    _name = 'hr.overtime.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "work_type_id"


    employee_id = fields.Many2one("hr.employee", string="Employee", track_visibility="always")
    description = fields.Text(string="Reason", track_visibility="always")
    state = fields.Selection([('draft', 'Draft'),
                              ('submitted', 'Waiting for Confirmation'),
                              ('confirmed', 'Waiting for Verification'),
                              ('verified', 'Waiting for Approval'),
                              ('approved', 'Approved'),
                              ('canceled', 'Cancelled')], string="Status",
                              copy=False, track_visibility="always")

    overtime_id = fields.Many2one('hr.overtime', ondelete='cascade')
    start_date = fields.Datetime(string="Start", required=True, track_visibility="always")
    end_date = fields.Datetime(string="End", required=True, track_visibility="always")
    hours = fields.Float(string="Duration", track_visibility="always")
    rendered_hours = fields.Float(string="Rendered Hours", track_visibility="always")
    overtime_work_date = fields.Date(string="Work Date", track_visibility="always")
    work_type_id = fields.Many2one('hr.overtime.type', string="Code", track_visibility="always")
    code = fields.Selection([('OT','Ordinary Overtime (125%)'),
                             ('OTND','Ordinary Overtime + Night Differential'),
                             ('RD','Restday'),
                             ('RHD','Regular Holiday (200%)'),
                             ('SHD','Special Holiday (130%)'),
                             ('DHD','Double Holiday'),
                             ('RHDOT','Regular Holiday Overtime (260%)'),
                             ('SHDOT','Special Holiday Overtime (169%)'),
                             ('DHDOT','Double Holiday + Overtime'),
                             ('RHDND','Regular Holiday + Night Differential'),
                             ('SHDND','Special Holiday + Night Differential'),
                             ('DHDND','Double Holiday + Night Differential'),
                             ('RHDOTND','Regular Holiday + Night Differential + Overtime'),
                             ('SHDOTND','Special Holiday + Night Differential + Overtime'),
                             ('DHDOTND','Double Holiday + Night Differential + Overtime'),
                             ('RDOT','Restday + Overtime'),
                             ('RDND','Restday + Night Differential'),
                             ('RDOTND','Restday + Night Differential + Overtime'),
                             ('RHDRD','Regular Holiday + Restday'),
                             ('SHDRD','Special Holiday + Restday'),
                             ('DHDRD','Double Holiday + Restday'),
                             ('RHDRDOT','Regular Holiday + Restday + Overtime'),
                             ('SHDRDOT','Special Holiday + Restday + Overtime'),
                             ('DHDRDOT','Double Holiday + Restday + Overtime'),
                             ('RHDRDND','Regular Holiday + Restday + Night Differential'),
                             ('SHDRDND','Special Holiday + Restday + Night Differential'),
                             ('DHDRDND','Double Holiday + Restday + Night Differential'),
                             ('RHDRDOTND','Regular Holiday + Restday + Night Differential + Overtime'),
                             ('SHDRDOTND','Special Holiday + Restday + Night Differential + Overtime'),
                             ('DHDRDOTND','Double Holiday + Restday + Night Differential + Overtime'),
                             ],string="Overtime Name", related="work_type_id.code")

    @api.multi
    def unlink(self):
        for i in self:
            if i.overtime_id and i.overtime_id.state == "approved":
                raise ValidationError(_("Please Delete first the source data of this record."))
            super(HROvertimeLine, i).unlink()


class HROvertime(models.Model):
    _name = 'hr.overtime'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin', 'document.default.approval']
    _rec_name = "name"

    employee_id = fields.Many2one(string="Employee", comodel_name="hr.employee", required=True,
                                  readonly=True, states={'draft': [('readonly', False)]}, track_visibility="always")
    company_id = fields.Many2one('res.company', string="Company", related="employee_id.company_id")
    request_date = fields.Date(string="Request Date", default=date.today(), track_visibility="always")
    work_type_ids = fields.One2many('hr.overtime.line', 'overtime_id',
                                    string="Work Type", readonly=True,
                                    states={'draft': [('readonly', False)]}, track_visibility="always")
    overtime_start = fields.Datetime(string="Overtime Start", readonly=True, states={'draft': [('readonly', False)]},
                                     required=True, track_visibility="always")
    overtime_end = fields.Datetime(string="Overtime End",
                                   readonly=True, states={'draft': [('readonly', False)]},
                                   required=True, track_visibility="always")
    overtime_work_date = fields.Date(string="Work Date")
    hours = fields.Float(string="Total Hours", track_visibility="always")
    description = fields.Text(string="Reason", required=True,
                       readonly=True, states={'draft': [('readonly', False)]},
                       track_visibility="always")
    name = fields.Char(string="Reference", default="/")

    @api.multi
    def approve_request(self):
        for i in self:
            for rec in i.work_type_ids:
                rec.write({'description': i.description, 'employee_id': i.employee_id.id, 'overtime_work_date': i.overtime_work_date, 'state': "approved"})
            super(HROvertime, i).approve_request()

    @api.multi
    def submit_request(self):
        for i in self:
            super(HROvertime, i).submit_request()
            i.write({'name': self.env['ir.sequence'].get('overtime.request')})
            if i.employee_id.parent_id and i.employee_id.parent_id.user_id:
                activity_record = {
                    'activity_type_id': 5,
                    'res_id': i.id,
                    'res_model_id': i.env['ir.model'].search([('model', '=', 'hr.overtime')], limit=1).id,
                    'date_deadline': i.overtime_start,
                    'user_id': i.employee_id.parent_id.user_id.id,
                    'note': i.name,
                    'summary': 'For Approval',
                    }
                i.env['mail.activity'].create(activity_record)
            i.write({
                'state': 'submitted',
            })
            i.add_follower(i.employee_id.id)
            msg_body = '''%s is requesting for an Overtime Work:
            <br/>Date:  %s to %s
            <br/>Total Hours: %s
            <br/>Reason: <br/><ul>%s</ul>'''%(i.employee_id.name, (i.overtime_start).strftime(DF), (i.overtime_end).strftime(DF),convert_to_time(i.hours),i.name)
            i.message_post(body=msg_body,subject="Overtime Work Request")
        return True

    @api.multi
    def compute_time(self):
        for i in self:
            if i.overtime_start and i.overtime_end and i.employee_id:
                for rec in i.work_type_ids:
                    rec.unlink()
                i.write({'work_type_ids': i._check_filed_time()})
        return True

    @api.multi
    def add_follower(self, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)
        partner_ids = []
        if employee.parent_id and employee.parent_id.user_id:
            partner_ids.append(employee.parent_id.user_id.partner_id.id)
        if employee.user_id:
            partner_ids.append(employee.user_id.partner_id.id)
        if partner_ids:
            self.message_subscribe(partner_ids=partner_ids)

    @api.model
    def create(self, vals):
        res = super(HROvertime, self.with_context(mail_create_nolog=True, mail_create_nosubscribe=True)).create(vals)
        res.compute_time()
        return res

    @api.multi
    def write(self, vals):
        super(HROvertime, self).write(vals)
        if vals.get('overtime_start') or vals.get('overtime_end') or vals.get('employee_id'):
            self.compute_time()


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

    @api.multi
    def _holiday_type(self, date, employee):
        holidays = self.env['company.holiday'].search([('date','=',date)])
        holiday_type = ''
        holiday_count = 0
        for i in holidays:
            for rec in i.company_ids:
                if employee.contract_id.company_id.id == rec.id:
                    holiday_count += 1
                    holiday_type = i.holiday_type
        if holiday_count == 0: return holiday_type
        if holiday_count >= 2: return "DHD"
        elif holiday_type == 'Regular': return "SHD"
        else: return "SHD"

    @api.multi
    def get_date_schedule(self, employee, date):
        schedule = self.env['resource.calendar.attendance']
        res = {'schedule_start': False, 'schedule_end': False}
        sched_ids = [i.id for i in schedule.search([('calendar_id', '=', employee.contract_id.resource_calendar_id.id), ('dayofweek', '=', date.weekday())])]
        if sched_ids:
            res['schedule_start'] = datetime.combine(date, time(int(divmod((schedule.browse(min(sched_ids)).hour_from * 60), 60)[0]),int(divmod((schedule.browse(min(sched_ids)).hour_from * 60), 60)[1])))
            if schedule.browse(min(sched_ids)).hour_from > schedule.browse(max(sched_ids)).hour_to:
                date += timedelta(days=1)
            res['schedule_end'] = datetime.combine(date, time(int(divmod((schedule.browse(max(sched_ids)).hour_to * 60), 60)[0]),int(divmod((schedule.browse(max(sched_ids)).hour_to * 60), 60)[1])))

        return res

    @api.multi
    def get_night_differential_hours(self,work_schedule, overtime_start, overtime_end, nd_start, nd_end):
        total_hours = 0
        night_differential_start = datetime(work_schedule.year, work_schedule.month, work_schedule.day, int(divmod((nd_start * 60), 60)[0]), int(divmod((nd_start * 60), 60)[1]))
        night_differential_end = datetime(work_schedule.year, work_schedule.month, work_schedule.day + 1, int(divmod((nd_end * 60), 60)[0]), int(divmod((nd_end * 60), 60)[1]))
        night_differential_time_start = overtime_start
        night_differential_time_end = overtime_end
        if overtime_start < night_differential_start:
            overtime_start = night_differential_start
            night_differential_time_start = night_differential_start
        if overtime_end > night_differential_start:

            if overtime_end > night_differential_end:
                total_hours = compute_hour_difference(overtime_start, night_differential_end)
                night_differential_time_end = night_differential_end
            else:
                total_hours = compute_hour_difference(overtime_start, overtime_end)
        return {'total_hours': total_hours > 0.0 and total_hours or 0.0, 'time_start': night_differential_time_start, 'time_end': night_differential_time_end}

    @api.multi
    def check_minimum_overtime(self, overtime_start, overtime_end):
        if compute_hour_difference(overtime_start, overtime_end) < self.env.user.company_id.minimum_overtime_file:
            raise ValidationError(_("Minimum Overtime is %s hours"%(convert_to_time(self.env.user.company_id.minimum_overtime_file))))
        return True

    @api.multi
    def _check_filed_time(self):
        work_schedules = []
        contract_schedule = self.employee_id.contract_id.resource_calendar_id
        # Get the set Night Differential Hours parameters
        nd_start = self.env.user.company_id.nightdiff_hour_start
        nd_end = self.env.user.company_id.nightdiff_hour_end
        # Overtime overtime_start and overtime_end Paremeters
        overtime_start = self.overtime_start  + timedelta(hours=contract_schedule.utc_offset)
        overtime_end = self.overtime_end + timedelta(hours=contract_schedule.utc_offset)
        # Parsing Datetime to Date
        overtime_date = datetime.strptime(self.overtime_start.strftime(DF), DF)
        date_schedule = self.get_date_schedule(self.employee_id, overtime_date)
        #check the minimum Overtime Hours
        self.check_minimum_overtime(overtime_start, overtime_end)

        holiday_type = self._holiday_type(overtime_date, self.employee_id)
        work_types = self.env['hr.overtime.type']
        ot_hours = compute_hour_difference(overtime_start, overtime_end)
        if date_schedule.get('schedule_end'):
            if date_schedule.get('schedule_end').strftime(DT) > overtime_start.strftime(DT) and holiday_type in [False, '']:
                raise ValidationError(_("Valid Overtime should after %s"%(date_schedule.get('schedule_end').strftime(DT))))
        # _logger.info("\n\nData \t%s"%(str(night_differential)))
        work_schedule = date_schedule.get('schedule_start') and date_schedule.get('schedule_start') or overtime_start
        night_differential = self.get_night_differential_hours(work_schedule, overtime_start, overtime_end, nd_start, nd_end)
        if date_schedule.get('schedule_start'):
            #In work schedules, iether Holiday or Not.
            self.write({'overtime_work_date': date_schedule.get('schedule_start').strftime(DF)})
            search_param = holiday_type + 'OT'
            work_type = work_types.search([('code','=',search_param)])
            work_schedules.append([overtime_start, overtime_end, ot_hours, work_type.id])
            #Check for Night Differentials

            if night_differential.get('total_hours') > 0.00:
                ot_start, ot_end = night_differential.get('time_start'), night_differential.get('time_end')
                ot_hours = night_differential.get('total_hours')
                work_type = work_types.search([('code', '=', holiday_type + 'OTND')])
                work_schedules.append([ot_start, ot_end, ot_hours, work_type.id])
        else:
            self.write({'overtime_work_date': overtime_start.strftime(DF)})
            search_param = holiday_type + 'RD'
            restday = ot_hours
            if ot_hours <= contract_schedule.restday_workhours:
                if night_differential.get('total_hours') > 0.00:
                    ot_start, ot_end = night_differential.get('time_start'), night_differential.get('time_end')
                    ot_hours = night_differential.get('total_hours')
                    work_type = work_types.search([('code', '=', holiday_type + 'RDND')])
                    work_schedules.append([ot_start, ot_end, ot_hours, work_type.id])
                work_type = work_types.search([('code','=',search_param)])
                work_schedules.append([overtime_start, overtime_end, ot_hours, work_type.id])
            else:
                restday_rendered = contract_schedule.restday_workhours
                restday_end = overtime_start + timedelta(hours=(contract_schedule.restday_workhours))
                work_type = work_types.search([('code','=',search_param)])
                work_schedules.append([overtime_start, restday_end, restday_rendered, work_type.id])
                # Reintialize night_differential parameters set overtime_start time to -> rd_end
                #NOTE: Restday computation will not deduct the Breatime Hours.
                #TODO: Create a config settings that will allow the user to set -> Deduct Breatime hours on the restday.
                rd_night_differential = self.get_night_differential_hours(work_schedule, overtime_start, restday_end, nd_start, nd_end)
                if rd_night_differential.get('total_hours') > 0.00:
                    ot_start, ot_end = rd_night_differential.get('time_start'), rd_night_differential.get('time_end')
                    ot_hours = rd_night_differential.get('total_hours')
                    work_type = work_types.search([('code', '=', holiday_type + 'RDND')])
                    work_schedules.append([ot_start, ot_end, ot_hours, work_type.id])
                search_param = search_param +'OT'
                work_type = work_types.search([('code','=',search_param)])
                work_schedules.append([restday_end, overtime_end, restday - restday_rendered, work_type.id])
                rdot_night_differential = self.get_night_differential_hours(work_schedule, overtime_start, overtime_end, nd_start, nd_end)
                if rdot_night_differential.get('total_hours') > 0.00:
                    ot_start, ot_end = rdot_night_differential.get('time_start'), rdot_night_differential.get('time_end')
                    ot_hours = rdot_night_differential.get('total_hours')
                    work_type = work_types.search([('code', '=', holiday_type + 'RDOTND')])
                    work_schedules.append([ot_start, ot_end, ot_hours, work_type.id])
        work_schedule_data = []
        for i in work_schedules:
            work_schedule_data.append([0, 0,{'start_date': i[0] - timedelta(hours=contract_schedule.utc_offset),
                                             'end_date': i[1] - timedelta(hours=contract_schedule.utc_offset),
                                             'hours': i[2],
                                             'work_type_id': i[3]
                                             }])
        return work_schedule_data

    @api.constrains('employee_id', 'overtime_start', 'overtime_end')
    def _check_ot_parameter(self):
        if self.employee_id and self.overtime_start and self.overtime_end:
            contract = self.get_contract(self.employee_id, self.overtime_start, self.overtime_end)
            if not contract:
                raise ValidationError(_("No valid employment contract found for %s."%(self.employee_id.name)))
            contract_schedule = self.employee_id.contract_id.resource_calendar_id
            overtime_start = self.overtime_start  + timedelta(hours=contract_schedule.utc_offset)
            overtime_end = self.overtime_end + timedelta(hours=contract_schedule.utc_offset)
            overtime_date = datetime.strptime(self.overtime_start.strftime(DF), DF)
            date_schedule = self.get_date_schedule(self.employee_id, overtime_date)
            if date_schedule.get('schedule_end'):
                holiday_type = self._holiday_type(overtime_date, self.employee_id)
                if date_schedule.get('schedule_end').strftime(DT) > overtime_start.strftime(DT) and holiday_type in [False, '']:
                    raise ValidationError(_("Valid Overtime should after %s - %s"%(date_schedule.get('schedule_end').strftime(DT), holiday_type)))



    # @api.onchange('employee_id', 'overtime_start')
    # def _onchange_work_parameter(self):
    #     if self.employee_id and self.overtime_start:
    #         #Check if there is a valid contract.
    #         contract = self.get_contract(self.employee_id, self.overtime_start, self.overtime_end)
    #         if not contract:
    #             raise ValidationError(_("No valid employment contract found for %s."%(self.employee_id.name)))
