# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta, time
import time as tm
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
import logging
_logger = logging.getLogger("_name_")

# Decimal to time format
def convert_to_time(dec_hours):
    seconds = dec_hours * 60 * 60
    return tm.strftime("%H:%M:%S", tm.gmtime(seconds))

class HROBLine(models.Model):
    _name = 'hr.ob.line'
    _rec_name = 'ob_id'

    ob_id = fields.Many2one("hr.official.business", string="Official Business", index=True, ondelete='cascade')
    time_start = fields.Float(string="From", required=True)
    time_end = fields.Float(string="To", required=True)
    location_origin = fields.Char(string="Origin", required=True)
    location_destination = fields.Char(string="Destination", required="True")
    name = fields.Text(string="Purpose")


class HROfficialBusiness(models.Model):
    _name = 'hr.official.business'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin', 'document.default.approval']

    name = fields.Char(string="Reference", default="/", copy=False)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True,
                                  states={'draft': [('readonly', False)]}, required=True,
                                  track_visibility="always")
    contract_id = fields.Many2one('hr.contract', string="Contrart",
                                  readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string="Company", related="employee_id.company_id")
    department_id = fields.Many2one('hr.department', string="Department", related="contract_id.department_id")
    job_id = fields.Many2one('hr.job', string="Position", related="contract_id.job_id")
    filing_date = fields.Date(string="Filing Date", required=True, default=fields.Date.context_today, track_visibility="always")
    ob_date = fields.Date(string="Official Busness Date", required=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility="always")
    date_start = fields.Datetime(string="OB From", compute="_get_datetime_data", store=True, track_visibility="always")
    date_end = fields.Datetime(string="OB From", compute="_get_datetime_data", store=True, track_visibility="always")
    ob_line_ids = fields.One2many("hr.ob.line", "ob_id", string="Itenerary", track_visibility="always")

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

    @api.onchange("employee_id", "ob_date")
    def _onchange_employee(self):
        if self.employee_id and self.ob_date:
            contract = self.get_contract(self.employee_id, self.ob_date - timedelta(days=1), self.ob_date + timedelta(days=1))
            if not contract:
                raise ValidationError(_("No valid employment contract found."))
            self.contract_id = contract[0]

    @api.constrains("employee_id", "ob_line_ids", "ob_line_ids.time_start", "ob_line_ids.time_end", "ob_date")
    def _check_data(self):
        if self.employee_id and self.ob_date:
            if not self.contract_id:
                raise ValidationError(_("No valid employment contract found."))
            if len(self.ob_line_ids) > 0:
                for rec in self.ob_line_ids:
                    if rec.time_start >= 24.00 or rec.time_start < 0.00 or rec.time_end >= 24.00 or rec.time_end < 0.00:
                        raise ValidationError(_("Invalid Time Input."))
            else: raise ValidationError(_("Official Busness' Itenerary is required."))

    @api.depends("ob_line_ids", "ob_line_ids.time_start", "ob_line_ids.time_end", "ob_date", "contract_id")
    def _get_datetime_data(self):
        for i in self:
            if i.ob_date and len(i.ob_line_ids) > 0 and i.employee_id:
                date = i.ob_date
                dates = []
                _logger.info("\n\n\nData: %s\n\n\n"%(str(min(i.ob_line_ids))))
                for rec in i.ob_line_ids:
                    start_time = rec.time_start
                    end_time = rec.time_end
                    dates.append(datetime.strptime("%s %s"%(date.strftime(DF), convert_to_time(start_time)), DT) - timedelta(hours=self.contract_id.resource_calendar_id.utc_offset))
                    if start_time > end_time:
                        date = i.ob_date + timedelta(days=1)
                    dates.append(datetime.strptime("%s %s"%(date.strftime(DF), convert_to_time(end_time)), DT) - timedelta(hours=self.contract_id.resource_calendar_id.utc_offset))
                i.date_start = min(dates)
                i.date_end = max(dates)

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
        res = super(HROfficialBusiness, self).submit_request()
        self.write({'name': self.env['ir.sequence'].get('offical.business')})
        self.add_follower(self.employee_id.id)
        itenerary = ''
        for i in self.ob_line_ids:
            itenerary += """
                <tr class="info">
                    <td>
                        <strong class="text-center"><em>%s</em></strong>
                    </td>
                    <td>
                        <strong class="text-center"><em>%s</em></strong>
                    </td>
                    <td>
                        <strong class="text-center"><em>%s</em></strong>
                    </td>
                    <td>
                        <strong class="text-center"><em>%s</em></strong>
                    </td>
                    <td>
                        <strong class="text-center"><em>%s</em></strong>
                    </td>
                </tr>
            """%(i.location_origin, i.location_destination, i.name, convert_to_time(i.time_start), convert_to_time(i.time_end))
        msg_body = '''%s is requesting approval for an Official Busness:
        <br/>Datetime:  %s to %s
        <br/>Itenerary:
        <br/><ul>
                <table class="table table-striped table-hover" colspan="2">
                    <tr class="info">
                        <td>
                            <strong class="text-center">Origin</strong>
                        </td>
                        <td>
                            <strong class="text-center">Destination</strong>
                        </td>
                        <td>
                            <strong class="text-center">Purpose</strong>
                        </td>
                        <td>
                            <strong class="text-center">From</strong>
                        </td>
                        <td>
                            <strong class="text-center">To</strong>
                        </td>
                    </tr>
                    %s
                </table>
            </ul>'''%(self.employee_id.name,(self.date_start + timedelta(hours=8)).strftime(DT) , (self.date_end + timedelta(hours=8)).strftime(DT), itenerary)
        self.message_post(body=msg_body,subject="Official Busness - for Approval")
        return res
