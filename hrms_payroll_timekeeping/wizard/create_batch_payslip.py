# -*- coding: utf-8 -*-
'''
Created on 25 of January 2020
@author: Dennis
'''
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, tools, SUPERUSER_ID, _

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    @api.multi
    def additional_data(self, data):
        payroll = self.env['hr.payslip.run'].browse(self._context.get('active_id'))
        attendance_summary = self.env['hr.attendance.summary.line'].search([
                                            ('employee_id', '=', data.get('employee_id')),
                                            ('attendance_summary_id', '=', payroll.attendance_summary_id.id)],
                                            limit=1)
        if attendance_summary[:1]:
            data['employee_attendance_summary'] = attendance_summary.id
        else:
            employee = self.env['hr.employee'].browse(data.get('employee_id'))
            raise ValidationError(_("No attendance summary found for %s"%(employee.name)))
        return data
