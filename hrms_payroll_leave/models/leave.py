'''
Created on 02 of Jan 2020

@author: Dennis
'''

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta

import logging
_logger = logging.getLogger("_name_")


class HRLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    @api.multi
    def _get_default_year(self):
        for i in self:
            i.calendar_year = date.today().year

    calendar_year = fields.Char(string="Year Valid", required=True, default=_get_default_year)

    @api.constrains('calendar_year')
    def check_year(self):
        if self.calendar_year:
            if not self.calendar_year.isdigit():
                raise ValidationError(_('Invalid "Year Valid" input.\nMust be an Integer.'))

class HRLeave(models.Model):
    _inherit = "hr.leave"

    @api.depends('request_date_from')
    def _get_year(self):
        for i in self:
            if i.request_date_from:
                i.calendar_year = i.request_date_from.year

    calendar_year = fields.Char(string="Year Valid", store=True, compute="_get_year")

    @api.constrains('request_date_from', 'request_date_to', 'holiday_status_id')
    def check_leave_constrains(self):
        if self.request_date_from and self.request_date_to and self.holiday_status_id:
            if self.request_date_from.year != self.request_date_to.year and self.holiday_status_id.allocation_type == 'forfeitable':
                raise ValidationError(_('Filing Leaves must be within the same year.'))
            if not self.holiday_status_id.post_filling and  (self.request_date_from - date.today()).days < self.holiday_status_id.days_required_to_file:
                raise ValidationError(_('Filing Leaves must be done %s days prior to leave date'%(self.holiday_status_id.days_required_to_file)))

class HRLeaveType(models.Model):
    _inherit = "hr.leave.type"

    leave_allocation_type = fields.Selection([('forfeitable', 'Forfeitable by the End of Year'), ('commulative', 'Commulative')], required=True, string="Allocation Type", default="forfeitable")
    convertable_to_cash = fields.Boolean(string="Convertable to Cash", help="Payout via Payroll")
    rule_code = fields.Char(string="Code", help="Code to use in the Salary Rule computations.", size=10, default='NONE')
    days_required_to_file = fields.Integer(string="Validation Days", help="Validation for leaves days before filing", default=5)
    post_filling = fields.Boolean(string="Allow Post-filing")


class HRPayrollLeaveSummary(models.Model):
    _name = 'hr.payroll.leave.summary'
    _description = 'Leave summary for payable'

    @api.depends('allocation', 'used')
    def _get_leave_balance(self):
        for i in self:
            i.remaining = i.allocation - i.used

    payslip_id = fields.Many2one('hr.payslip', string="Slip", ondelete='cascade')
    leave_type_id = fields.Many2one('hr.leave.type', string="Leave Type")
    allocation = fields.Float(string="Allocation")
    used = fields.Float(string="Used")
    remaining = fields.Float(string="Remaining", store=True, compute="_get_leave_balance")

class HRPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    convert_leave = fields.Boolean(string="Convert Leaves")

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    convert_leave = fields.Boolean(string="Convert Leaves")
    payable_leave_ids = fields.One2many('hr.payroll.leave.summary', 'payslip_id', string="Payable Leaves")

    @api.multi
    def action_payslip_done(self):
        res = super(HRPayslip, self).action_payslip_done()
        self.env['hr.employee'].forfeite_unused_leaves(self.employee_id.id)
        return res

    @api.model
    def get_payable_leaves(self, employee, date_from, date_to):
        leaves = []
        leave_records = self.env['hr.leave.report'].search(
                                                [('employee_id', '=', employee.id),
                                                 ('calendar_year', '=', date_from.year),
                                                 ('holiday_status_id.leave_allocation_type', '=', 'forfeitable'),
                                                 ('holiday_status_id.convertable_to_cash', '=', True),
                                                 ('state', '=', 'validate'),
                                                 ('number_of_days', '!=', 0)])
        for rec in leave_records:
            found = False
            for i in leaves:
                if i['leave_type_id'] == rec.holiday_status_id.id:
                    found = True
                    if rec.type == 'allocation':
                        i['allocation'] = i.get('allocation') + rec.number_of_days
                    else:
                        i['used'] = i.get('used') + abs(rec.number_of_days)

            if not found:
                data = {'leave_type_id': rec.holiday_status_id.id}
                if rec.type == 'allocation':
                    data['allocation'] = rec.number_of_days
                    data['used'] = 0
                else:
                    data['used'] = abs(rec.number_of_days)
                    data['allocation'] = 0
                leaves.append(data)
        return leaves

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(HRPayslip, self).get_inputs(contracts, date_from, date_to)
        for contract in contracts:
            daily_wage = (contract.wage * 12.00) / float(contract.resource_calendar_id.year_days)
            for i in self.payable_leave_ids:
                input_data = {
                    'name': i.leave_type_id.name,
                    'code': i.leave_type_id.rule_code,
                    'amount': i.remaining * daily_wage,
                    'contract_id': contract.id,
                }
                res += [input_data]
        return res


    @api.onchange('employee_id', 'date_from', 'date_to', 'convert_leave')
    def onchange_employee(self):
        leave_ids = []
        if self.convert_leave:
            leave_ids = self.get_payable_leaves(self.employee_id, self.date_from, self.date_to)
        leave_lines = self.payable_leave_ids.browse([])
        for r in leave_ids:
            leave_lines += leave_lines.new(r)
        self.payable_leave_ids = leave_lines
        super(HRPayslip, self).onchange_employee()


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def forfeite_unused_leaves(self, employee_id):
        leaves = []
        leave_records = self.env['hr.leave.report'].search(
                                                [('employee_id', '=', employee_id),
                                                 # ('calendar_year', '=', date.today().year),
                                                 ('holiday_status_id.leave_allocation_type', '=', 'forfeitable'),
                                                 ('state', '=', 'validate')], order="document_id desc")
        for rec in leave_records:
            found = False
            for i in leaves:
                if i['leave_type_id'] == rec.holiday_status_id.id:
                    found = True
                    if rec.type == 'allocation':
                        i['allocation'] = i.get('allocation') + rec.number_of_days
                        i['ids'] = i.get('ids').append(rec.document_id)
                    else:
                        i['used'] = i.get('used') + rec.number_of_days
            if not found:
                data = {'leave_type_id': rec.holiday_status_id.id}
                if rec.type == 'allocation':
                    data['ids'] = [rec.document_id]
                    data['allocation'] = rec.number_of_days
                    data['used'] = 0
                else:
                    data['used'] = rec.number_of_days
                    data['allocation'] = 0
                leaves.append(data)
        # Forfeite Remaining leaves
        for rec in leaves:
            remaining = rec['allocation'] - rec['used']
            if remaining > 0:
                if rec.get('ids'):
                    for allocation in self.env['hr.leave.allocation'].browse(rec.get('ids')):
                        if remaining > 0:
                            if allocation.number_of_days < remaining:
                                allocation.write({'number_of_days': 0})
                                msg_body = "Forfeited Number of Leave: %s"%(allocation.number_of_days)
                                remaining -= allocation.number_of_days
                            else:
                                allocation.write({'number_of_days': allocation.number_of_days - remaining})
                                msg_body = "Forfeited Number of Leave: %s"%(remaining)
                            allocation.message_post(body=msg_body,subject="Forfeiting Leave Allocation")
                        else: continue
        # raise ValidationError(_('Data'))

class LeaveReport(models.Model):
    _inherit = "hr.leave.report"

    calendar_year = fields.Char(string="Year Valid")
    document_id = fields.Integer(string="Document Id")

    def init(self):
        tools.drop_view_if_exists(self._cr, 'hr_leave_report')

        self._cr.execute("""
            CREATE or REPLACE view hr_leave_report as (
                SELECT row_number() over(ORDER BY leaves.employee_id) as id,
                leaves.employee_id as employee_id, leaves.name as name,
                leaves.number_of_days as number_of_days, leaves.type as type,
                leaves.category_id as category_id, leaves.department_id as department_id,
                leaves.holiday_status_id as holiday_status_id, leaves.state as state,
                leaves.holiday_type as holiday_type, leaves.date_from as date_from,
                leaves.date_to as date_to, leaves.payslip_status as payslip_status,
                leaves.calendar_year as calendar_year, leaves.document_id as document_id
                from (select
                    allocation.employee_id as employee_id,
                    allocation.name as name,
                    allocation.number_of_days as number_of_days,
                    allocation.category_id as category_id,
                    allocation.department_id as department_id,
                    allocation.holiday_status_id as holiday_status_id,
                    allocation.state as state,
                    allocation.holiday_type,
                    null as date_from,
                    null as date_to,
                    FALSE as payslip_status,
                    'allocation' as type,
                    allocation.calendar_year as calendar_year,
                    allocation.id as document_id
                from hr_leave_allocation as allocation
                union all select
                    request.employee_id as employee_id,
                    request.name as name,
                    (request.number_of_days * -1) as number_of_days,
                    request.category_id as category_id,
                    request.department_id as department_id,
                    request.holiday_status_id as holiday_status_id,
                    request.state as state,
                    request.holiday_type,
                    request.date_from as date_from,
                    request.date_to as date_to,
                    request.payslip_status as payslip_status,
                    'request' as type,
                    request.calendar_year as calendar_year,
                    request.id as document_id
                from hr_leave as request) leaves
            );
        """)

    def _read_from_database(self, field_names, inherited_field_names=[]):
        if 'name' in field_names and 'employee_id' not in field_names:
            field_names.append('employee_id')
        super(LeaveReport, self)._read_from_database(field_names, inherited_field_names)
        if 'name' in field_names:
            if self.user_has_groups('hr_holidays.group_hr_holidays_user'):
                return
            current_employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
            for record in self:
                emp_id = record._cache.get('employee_id', [False])[0]
                if emp_id != current_employee.id:
                    try:
                        record._cache['name']
                        record._cache['name'] = '*****'
                    except Exception:
                        # skip SpecialValue (e.g. for missing record or access right)
                        pass
