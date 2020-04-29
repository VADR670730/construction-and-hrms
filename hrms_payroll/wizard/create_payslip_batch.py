
'''
Created on 08 of December 2019

@author: Dennis
'''

from odoo import api, fields, models, tools, SUPERUSER_ID, _

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'

    company_id = fields.Many2one('res.company', string="Company/Branch")
    cutoff_template_id = fields.Many2one('payroll.cutoff.template', string="Attendance Cutoff Group")
    valid_employee_ids = fields.Many2many('hr.employee', 'valid_employee_rel', string="Valid Employee")

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
        res = super(HrPayslipEmployees, self).default_get(fields)
        data = self.env['hr.payslip.run'].browse(self._context.get('active_id'))
        res['company_id'] = data.company_id.id
        res['cutoff_template_id'] = data.cutoff_template_id.id
        employee_ids = []
        employee_rec = self.env['hr.employee'].search([('company_id', '=', data.company_id.id), ('active', '=', True)])
        for emp in employee_rec:
            contract_data = self.get_contract(emp, data.date_start, data.date_end)
            if contract_data:
                contract = self.env['hr.contract'].browse(max(contract_data))
                if contract.cutoff_template_id.id ==  data.cutoff_template_id.id:
                    employee_ids.append(emp.id)
        res['valid_employee_ids'] = employee_ids
        res['employee_ids'] = employee_ids
        return res

    @api.multi
    def additional_data(self, data):
        return data

    @api.multi
    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note', 'compute_thirtheenth_month', 'cutoff', 'month_year'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
                'company_id': self.company_id.id,
                'compute_thirtheenth_month': run_data.get('compute_thirtheenth_month'),
                'cutoff': run_data.get('cutoff'),
                'payslip_period': run_data.get('month_year'),

            }
            data = self.additional_data(res)
            payslips += self.env['hr.payslip'].create(data)
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}
