# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger("_name_")

class CreateEmployeeAttendance(models.TransientModel):
    _name = "create.employee.attendance"

    summary_id = fields.Many2one("hr.attendance.summary", string="Attendance Summary")
    employee_ids = fields.Many2many("hr.employee", 'attendance_employee_rel', string="Employee")
    valid_employee_ids = fields.Many2many('hr.employee', 'valid_attendance_employee_rel', string="Valid Employee")
    company_id = fields.Many2one('res.company', string="Company/Branch")
    cutoff_template_id = fields.Many2one('payroll.cutoff.template', string="Attendance Cutoff Group")

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

    @api.model
    def default_get(self, fields):
        res = super(CreateEmployeeAttendance, self).default_get(fields)
        data = self.env['hr.attendance.summary'].browse(self._context.get('active_id'))
        res['company_id'] = data.company_id.id
        res['cutoff_template_id'] = data.cutoff_template_id.id
        employee_ids = []
        employee_rec = self.env['hr.employee'].search([('company_id', '=', data.company_id.id), ('active', '=', True)])
        for emp in employee_rec:
            contract_data = self.get_contract(emp, data.date_from, data.date_to)
            if contract_data:
                contract = self.env['hr.contract'].browse(max(contract_data))
                if contract.cutoff_template_id.id ==  data.cutoff_template_id.id:
                    employee_ids.append(emp.id)
        res['valid_employee_ids'] = employee_ids
        res['employee_ids'] = employee_ids
        return res


    @api.multi
    def create_attendance_summary(self):
        if not self.employee_ids: raise ValidationError(_("Please select employee records."))
        data = []
        [i.unlink() for i in self.summary_id.line_ids]
        for i in self.employee_ids:
            dup_record = self.env['hr.attendance.summary.line'].search(["&","&",
                                                                            ('employee_id', '=', i.id),
                                                                            ('attendance_summary_id.state', 'not in', ['canceled']),
                                                                            "|",
                                                                                "&",
                                                                                    ('date_from', '>=', self.summary_id.date_from),
                                                                                    ('date_from', '<=', self.summary_id.date_to),
                                                                                "&",
                                                                                    ('date_to', '>=', self.summary_id.date_from),
                                                                                    ('date_to', '<=', self.summary_id.date_to),
                                                                        ], limit=1)
            if dup_record[:1]: raise ValidationError(_('Conflict of Record. Please see\nAttendance Summary:\t%s\nEmployee: \t%s'%(dup_record.attendance_summary_id.name, i.name)))
            data.append([0, 0, {
                'employee_id': i.id,
                'date_from': self.summary_id.date_from,
                'date_to': self.summary_id.date_to,
            }])
        self.summary_id.write({'line_ids': data})
        self.summary_id.compute_attendance()
