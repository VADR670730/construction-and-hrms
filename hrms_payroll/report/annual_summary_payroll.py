'''
Created on 08 of September 2019
@author: Dennis
'''
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import pandas as pd
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
import decimal
import logging
_logger = logging.getLogger("_name_")

def workbook_table_label(workbook):
    table_label = workbook.add_format()
    table_label.set_font_color('black')
    table_label.set_font_name('Arial')
    table_label.set_font_size(11)
    return table_label

def workbook_table_label_data(workbook):
    label_data = workbook.add_format()
    label_data.set_bold(True)
    label_data.set_font_color('black')
    label_data.set_font_name('Arial')
    label_data.set_font_size(12)
    label_data.set_center_across()
    label_data.set_align('left')
    return label_data


def workbook_table_header(workbook):
    table_header = workbook.add_format()
    table_header.set_bold(True)
    table_header.set_font_color('black')
    table_header.set_font_name('Arial')
    table_header.set_font_size(12)
    table_header.set_bg_color('#b5e9ff')
    table_header.set_center_across()
    table_header.set_align('vcenter')
    return table_header

def workbook_table_row_index(workbook):
    table_row = workbook.add_format()
    table_row.set_bold(True)
    table_row.set_font_color('black')
    table_row.set_font_name('Arial')
    table_row.set_font_size(11)
    table_row.set_bg_color('#cceeff')
    return table_row

def workbook_table_row(workbook):
    table_row = workbook.add_format()
    # table_row.set_bold(True)
    table_row.set_font_color('black')
    table_row.set_font_name('Arial')
    table_row.set_font_size(11)
    table_row.set_bg_color('#cceeff')
    table_row.set_num_format('#,##0.00_);(#,##0.00)')
    return table_row

def workbook_table_row_total(workbook):
    table_row = workbook.add_format()
    table_row.set_bold(True)
    table_row.set_font_color('black')
    table_row.set_font_name('Arial')
    table_row.set_font_size(11)
    table_row.set_bg_color('#cceeff')
    table_row.set_num_format('[$₱-3409]#,##0.00;[RED](-[$₱-3409]#,##0.00)')
    table_row.set_top(2)
    return table_row

class HRMSPayrollAnnualSummary(models.AbstractModel):
    _name = 'report.hrms_payroll.payroll_annual_summary'
    _inherit = 'report.report_xlsx.abstract'

    @api.multi
    def get_data(self, obj_data):
        try:
            date = datetime.strptime("%s-01-01"%(obj_data.year), DF)
            jan_date = datetime.strptime("%s-01-01"%(obj_data.year), DF) - timedelta(days=1)
            dec_date = datetime.strptime("%s-12-01"%(obj_data.year), DF) + timedelta(days=1)
        except:
            raise ValidationError(_('Year input is Invalid!'))
        data = []
        rec_domain = safe_eval(obj_data.domain)
        rec_domain += [
            ('slip_id.date_from', '>',jan_date),
            ('slip_id.date_from', '<',dec_date),
            ('slip_id.company_id', '=', obj_data.company_id.id),
            ('slip_id.state', 'in', ['done'])
            ]
        if  obj_data.employee_ids.ids:
            rec_domain += [('slip_id.employee_id', 'in', obj_data.employee_ids.ids)]
        for slip in self.env['hr.payslip.line'].search(rec_domain):
            if slip.total != 0.00:
                data.append({
                    'slip_month': "%s - %s"%((slip.slip_id.date_from).strftime("%B"), (slip.slip_id.date_from).year),
                    'payslip': slip.slip_id,
                    'payslip_name': slip.slip_id.name,
                    'payslip_cutoff': "%s - %s"%(slip.slip_id.date_from, slip.slip_id.date_to),
                    'employee': slip.slip_id.employee_id,
                    'employee_name': slip.slip_id.employee_id.name,
                    'employee_contract': slip.slip_id.contract_id.name,
                    'employee_type': slip.slip_id.contract_id.type_id.name,
                    'employee_job': slip.slip_id.contract_id.job_id.name,
                    'employee_department': slip.slip_id.contract_id.department_id.name,
                    'rule_category_name': slip.category_id.name,
                    'salary_rule': slip.salary_rule_id,
                    'salary_rule_name': slip.salary_rule_id.name,
                    'salary_rule_code': slip.salary_rule_id.code,
                    'salary_rule_sequence': slip.salary_rule_id.sequence,
                    'amount': decimal.Decimal(format(slip.total, '.2f')),
                })
        return data

    def get_employee_slip_detail(self, contract_slip):
        slip = pd.crosstab(index=[contract_slip.slip_month, contract_slip.payslip_cutoff], columns=[contract_slip.salary_rule_sequence,contract_slip.salary_rule_code,contract_slip.rule_category_name], values=contract_slip.amount, aggfunc='sum', margins=True).reset_index()
        slip.drop(slip.columns[len(slip.columns)-1], axis=1, inplace=True)
        return slip

    def generate_xlsx_report(self, workbook, data, line):
        table_label = workbook_table_label(workbook)
        table_label_data = workbook_table_label_data(workbook)
        table_label_data_datetime = table_label_data
        table_label_data_datetime.set_num_format('dd/mm/yyyy hh:mm AM/PM')
        table_header = workbook_table_header(workbook)
        table_row_index = workbook_table_row_index(workbook)
        table_row = workbook_table_row(workbook)
        table_row_total = workbook_table_row_total(workbook)
        for obj in line:
            data = self.get_data(line)
            if not data:  raise ValidationError(_("Payslip is Empty"))
            df = pd.DataFrame(data).sort_values(by=['salary_rule_sequence'])
            contract = set(df['employee_name'].values.tolist())

            for rec in contract:
                payslip_register = workbook.add_worksheet(rec)
                contract_slip = df[df.employee_contract == rec]
                slips = self.get_employee_slip_detail(contract_slip)
                total_contract = pd.crosstab(index=[contract_slip.employee_contract], columns=[contract_slip.salary_rule_sequence,contract_slip.salary_rule_code,contract_slip.rule_category_name], values=contract_slip.amount, aggfunc='sum', margins=True).reset_index()
                total_contract.drop(total_contract.columns[len(total_contract.columns)-1], axis=1, inplace=True)
                # total_contract.drop(total_contract.tail(1).index,inplace=True)
                header_cols = 0
                category = ''
                col_start = ''
                for i in slips:
                    column = i[2]
                    if i[0] == 'slip_month': column = 'Period'
                    elif i[0] == 'payslip_cutoff': column = 'Cutoff'
                    if category and category == i[2]:
                        payslip_register.merge_range(5, col_start, 5,header_cols, column, table_header)
                    else:
                        category = i[2]
                        col_start = header_cols
                        payslip_register.write(5, header_cols, column, table_header)
                    header_cols += 1
                header_cols = 0
                for i in slips:
                        payslip_register.write(6, header_cols,  i[1], table_header)
                        header_cols += 1
                payslip_register.merge_range(4, 0, 4, header_cols, "EMPLOYEE PAYROLL", table_label_data)
