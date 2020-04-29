'''
Created on 07 of September 2019
@author: Dennis
'''
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import pandas as pd
import io
import base64
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

class HRMSPayrollRegister(models.AbstractModel):
    _name = 'report.hrms_payroll.payroll_register'
    _inherit = 'report.report_xlsx.abstract'

    # @api.multi
    # def get_data(self, obj_data):
    #     payslip_data = []
    #     batch_ids = [i.id for i in obj_data.payslip_multi_batch_ids]
    #     # obj_data.payslip_multi_batch_ids.ids
    #     rec_domain = expression.AND([safe_eval(obj_data.domain)]) + [('slip_id.payslip_run_id', 'in', batch_ids)]
    #     for slip in self.env['hr.payslip.line'].search(rec_domain):
    #         payslip_data.append({
    #             'payslip': slip.slip_id,
    #             'employee': slip.slip_id.employee_id,
    #             'employee_name': slip.slip_id.employee_id.name,
    #             'employee_department': slip.slip_id.employee_id.department_id.name,
    #             'rule_category_name': slip.category_id.name,
    #             'salary_rule': slip.salary_rule_id,
    #             'salary_rule_name': slip.salary_rule_id.name,
    #             'salary_rule_code': slip.salary_rule_id.code,
    #             'salary_rule_sequence': slip.salary_rule_id.sequence,
    #             'amount': decimal.Decimal(format(slip.total, '.2f')),
    #         })
    #     return payslip_data

    @api.multi
    def get_data(self, obj_data):
        data = []
        if obj_data.batch_type == 'multi':
            rec_domain = [('slip_id.payslip_run_id', 'in', obj_data.payslip_multi_batch_ids.ids)]
        else:
            rec_domain = [('slip_id.payslip_run_id', '=', obj_data.payslip_batch_id.id)]
        if obj_data.employee_ids.ids:
            rec_domain += [('slip_id.employee_id', 'in', obj_data.employee_ids.ids)]
        rec_domain += expression.AND([safe_eval(obj_data.domain)])
        for slip in obj_data.env['hr.payslip.line'].search(rec_domain):
            if slip.total != 0:
                data.append({
                    'payslip': slip.slip_id,
                    'employee': slip.slip_id.employee_id,
                    'employee_name': slip.slip_id.employee_id.name,
                    'employee_department': slip.slip_id.employee_id.department_id.name,
                    'rule_category_name': slip.category_id.name,
                    'salary_rule': slip.salary_rule_id,
                    'salary_rule_name': slip.salary_rule_id.name,
                    'salary_rule_code': slip.salary_rule_id.code,
                    'salary_rule_sequence': slip.salary_rule_id.sequence,
                    'amount': slip.total,
                })
        # if not data:
        #     raise ValidationError(_('No valid data that matches your search criteria'))
        return data



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
            payslip_data = self.get_data(line)
            # if not payslip_data:  raise ValidationError(_("Payslip is Empty"))
            payslip_register = workbook.add_worksheet("Payslip Register")
            payslip_register.set_landscape()
            payslip_register.set_paper(14)
            payslip_register.set_column('A:A', 20)
            payslip_register.set_column('B:ZZ', 12)
            payslip_register.write(0, 0, "Company", table_label)
            payslip_register.merge_range(0, 1, 0, 3, obj.company_id.name, table_label_data)
            if obj.batch_type == 'single':
                payslip_register.write(1, 0, "Payroll Batch", table_label)
                payslip_register.merge_range(1, 1, 1, 3, obj.payslip_batch_id.name, table_label_data)
                payslip_register.write(2, 0, "Cutoff", table_label)
                payslip_register.merge_range(2, 1, 2, 3, "%s - %s"%(obj.payslip_batch_id.date_start, obj.payslip_batch_id.date_end), table_label_data)
            else:
                payslip_register.write(1, 0, "Payroll Batches", table_label)
                batch_name = [i.name for i in obj.payslip_multi_batch_ids]
                payslip_register.merge_range(1, 1, 1, 3, str(batch_name), table_label_data)
                payslip_register.write(2, 0, "Cutoff", table_label)
                cutoff = ["%s - %s"%(i.date_start, i.date_end) for i in obj.payslip_multi_batch_ids]
                payslip_register.merge_range(2, 1, 2, 3, str(cutoff), table_label_data)
            payslip_register.write(1, 4, "Run By", table_label)
            payslip_register.merge_range(1, 5, 1, 7, obj.create_uid.name, table_label_data)
            payslip_register.write(2, 4, "Run Date", table_label)
            payslip_register.merge_range(2, 5, 2, 7, datetime.now()+timedelta(hours=8), table_label_data_datetime)
            df = pd.DataFrame(payslip_data).sort_values(by=['salary_rule_sequence'])

            # EMPLOYEE PAYROLL
            crosstab_df = pd.crosstab(index=[df.employee_department,df.employee_name], columns=[df.salary_rule_sequence, df.salary_rule_code, df.rule_category_name], values=df.amount, aggfunc='sum', margins=True).reset_index()
            header_cols = 0
            crosstab_df.drop(crosstab_df.columns[len(crosstab_df.columns)-1], axis=1, inplace=True)
            category = ''
            col_start = ''
            for i in crosstab_df:
                if i[0] != 'employee_department':
                    if category and category == i[2]:
                        payslip_register.merge_range(5, col_start, 5,header_cols, i[0] == 'employee_name' and "Employee" or i[2], table_header)
                    else:
                        category = i[2]
                        col_start = header_cols
                        if i[0] == 'employee_name': payslip_register.merge_range(5, header_cols, 6,header_cols, "Employee", table_header)
                        else: payslip_register.write(5, header_cols, i[2], table_header)
                    header_cols += 1
            header_cols = 0
            for i in crosstab_df:
                if i[0] != 'employee_department':
                    payslip_register.write(6, header_cols, i[1] == 'employee_name' and "Employee" or i[1], table_header)
                    header_cols += 1
            payslip_register.merge_range(4, 0, 4, header_cols, "EMPLOYEE PAYROLL", table_label_data)
            rules = crosstab_df.values.tolist()
            data_rows = 7
            for rec in rules:
                data_cols = 0
                del rec[0]
                if not rec[0]:
                    for line in rec:
                        try:
                            payslip_register.write(data_rows, data_cols, line, data_cols == 0 and table_row_index or table_row_total)
                        except:
                            payslip_register.write(data_rows, data_cols, 0.00, data_cols == 0 and table_row_index or table_row_total)
                        data_cols += 1
                else:
                    for line in rec:
                        try:
                            payslip_register.write(data_rows, data_cols, line, data_cols == 0 and table_row_index or table_row)
                        except:
                            payslip_register.write(data_rows, data_cols, 0.00, data_cols == 0 and table_row_index or table_row)
                        data_cols += 1
                data_rows += 1

            # DEPARTMENT PAYROLL SUMMARY
            data_rows += 1
            payslip_register.merge_range(data_rows, 0, data_rows, header_cols, "DEPARTMENT PAYROLL SUMMARY", table_label_data)
            crosstab_summary_df = pd.crosstab(index=[df.employee_department], columns=[df.salary_rule_sequence, df.salary_rule_code, df.rule_category_name], values=df.amount, aggfunc='sum', margins=True).reset_index()
            header_cols = 0
            data_rows += 1
            crosstab_summary_df.drop(crosstab_summary_df.columns[len(crosstab_summary_df.columns)-1], axis=1, inplace=True)
            category = ''
            col_start = ''
            for i in crosstab_summary_df:
                if category and category == i[2]:
                    payslip_register.merge_range(data_rows, col_start, data_rows,header_cols, i[0] == 'employee_department' and "DEPARTMENT" or i[2], table_header)
                else:
                    category = i[2]
                    col_start = header_cols
                    if i[0] == 'employee_name': payslip_register.merge_range(data_rows, header_cols, data_rows + 1,header_cols, "Employee", table_header)
                    else: payslip_register.write(data_rows, header_cols, i[2], table_header)
                header_cols += 1
            header_cols = 0
            data_rows += 1
            for i in crosstab_summary_df:
                    payslip_register.write(data_rows, header_cols, i[0] == 'employee_department' and "DEPARTMENT" or i[1], table_header)
                    header_cols += 1

            rules = crosstab_summary_df.values.tolist()
            data_rows += 1
            for rec in rules:
                data_cols = 0
                if rec[0] == "All":
                    rec[0] = ''
                    for line in rec:
                        try:
                            payslip_register.write(data_rows, data_cols, line, data_cols == 0 and table_row_index or table_row_total)
                        except:
                            payslip_register.write(data_rows, data_cols, 0.00, data_cols == 0 and table_row_index or table_row_total)
                        data_cols += 1
                else:
                    for line in rec:
                        # _logger.info('\n\n\nData: \ndata:\n%s'%(str(line)))
                        try:
                            payslip_register.write(data_rows, data_cols, line, data_cols == 0 and table_row_index or table_row)
                        except:
                            payslip_register.write(data_rows, data_cols, 0.00, data_cols == 0 and table_row_index or table_row)
                        data_cols += 1
                data_rows += 1

            # for im in payslip_data:
            #     # payslip_register.write(data_rows, 1, 0.00, data_cols == 0 and table_row_index or table_row)
            #     buf_image=io.BytesIO(base64.b64decode(im.get('employee').image))
            #     payslip_register.insert_image('B%s'%(data_rows), "any_name.png", {'image_data': buf_image})
            #     data_rows += 1
