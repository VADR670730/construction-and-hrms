'''
Created on 06 of September 2019

@author: Dennis
'''
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger("_name_")

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'

    company_id = fields.Many2one('res.company', string="Company/Branch")

    @api.model
    def default_get(self, fields):
        res = super(HrPayslipEmployees, self).default_get(fields)
        data = self.env['hr.payslip.run'].browse(self._context.get('active_id'))
        res['company_id'] = data.company_id.id
        return res

class PayrollRegisterReport(models.TransientModel):
    _name = 'payroll.register.report'

    company_id = fields.Many2one('res.company', string="Company/Branch", required=True,
                                  default=lambda self: self.env['res.company']._company_default_get('payroll.register.report'))
    model_id = fields.Many2one(
        'ir.model', string='Model', index=True, required=True,
        default=lambda self: self.env.ref('hr_payroll.model_hr_salary_rule', raise_if_not_found=False))
    model_name = fields.Char(string='Model Name', related='model_id.model', readonly=True, store=True)
    domain = fields.Char(string='Filter', default='[]')
    year = fields.Integer(string="Year")

    report_type = fields.Selection([('Annual', 'Annual'), ('Payroll Register', 'Payroll Register')], string="Report Type", default="Payroll Register")
    batch_type = fields.Selection([('single', 'Single'), ('multi', 'Multi')], string="Payroll Batch", required=True, default='multi')


    payslip_multi_batch_ids = fields.Many2many('hr.payslip.run', string="Payroll Batch", domain="[('company_id', '=', company_id)]")
    payslip_batch_id = fields.Many2one('hr.payslip.run', string="Payroll Batch", domain="[('company_id', '=', company_id)]")
    employee_ids = fields.Many2many('hr.employee', 'report_payslip_employee_rel', string="Employee/s", domain="[('company_id', '=', company_id)]")
    date_start = fields.Date(string="Date From")
    date_end = fields.Date(string="Date To")

    @api.model
    def default_get(self, fields):
        res = super(PayrollRegisterReport, self).default_get(fields)
        res['year'] = datetime.now().year
        return res


    @api.onchange("payslip_batch_id")
    def _onchange_payslip_batch(self):
        if self.payslip_batch_id:
            self.employee_ids = [rec.employee_id.id for rec in self.payslip_batch_id.slip_ids]
            self.date_start = self.payslip_batch_id.date_start
            self.date_end = self.payslip_batch_id.date_end

    @api.multi
    def get_data(self):
        data = []
        if self.batch_type == 'multi':
            rec_domain = [('slip_id.payslip_run_id', 'in', self.payslip_multi_batch_ids.ids)]
        else:
            rec_domain = [('slip_id.payslip_run_id', '=', self.payslip_batch_id.id)]
        if self.employee_ids.ids:
            rec_domain += [('slip_id.employee_id', 'in', self.employee_ids.ids)]
        rec_domain += expression.AND([safe_eval(self.domain)])

        slip_record =self.env['hr.payslip.line'].search(rec_domain, limit=1)
        # for slip in self.env['hr.payslip.line'].search(rec_domain):
        #     data.append({
        #         'payslip': slip.slip_id,
        #         'employee': slip.slip_id.employee_id,
        #         'employee_name': slip.slip_id.employee_id.name,
        #         'employee_department': slip.slip_id.employee_id.department_id.name,
        #         'rule_category_name': slip.category_id.name,
        #         'salary_rule': slip.salary_rule_id,
        #         'salary_rule_name': slip.salary_rule_id.name,
        #         'salary_rule_code': slip.salary_rule_id.code,
        #         'salary_rule_sequence': slip.salary_rule_id.sequence,
        #         'amount': slip.total,
        #     })
        if not slip_record[:1]:
            raise ValidationError(_('No valid data that matches your search criteria'))
        return data

    @api.multi
    def generate_report(self):
        if self.report_type in ['Payroll Register']:
            # self.get_data()
            return self.env.ref('hrms_payroll.hrms_payroll_register_xlsx').report_action(self)
        else: return self.env.ref('hrms_payroll.hrms_payroll_annual_summary_xlsx').report_action(self)
