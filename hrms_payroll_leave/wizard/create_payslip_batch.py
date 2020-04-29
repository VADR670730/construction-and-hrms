
'''
Created on 08 of December 2019

@author: Dennis
'''

from odoo import api, fields, models, tools, SUPERUSER_ID, _

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'

    @api.multi
    def additional_data(self, data):
        run = self.env['hr.payslip.run'].browse(self._context.get('active_id'))
        if run.convert_leave:
            leave_ids = self.env['hr.payslip'].get_payable_leaves(self.env['hr.employee'].browse(data.get('employee_id')), data.get('date_from'), data.get('date_to'))
            data['payable_leave_ids'] = [[0, 0, i] for i in leave_ids]
        data['convert_leave'] = run.convert_leave
        data['payslip_run_id'] = self._context.get('active_id')
        return data
