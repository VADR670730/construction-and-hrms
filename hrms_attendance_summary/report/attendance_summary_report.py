# -*- coding: utf-8 -*-
'''
Created on 13 of January 2020
@author: Dennis
'''
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError\

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

def workbook_table_label_data_currency(workbook, currency):
    label_data = workbook.add_format()
    label_data.set_bold(True)
    label_data.set_font_color('black')
    label_data.set_font_name('Arial')
    label_data.set_font_size(12)
    label_data.set_center_across()
    label_data.set_align('left')
    label_data.set_num_format('[$'+currency+'-3409]#,##0.00;[RED](-[$'+currency+'-3409]#,##0.00)')
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

def workbook_table_row_percent(workbook):
    table_row = workbook.add_format()
    # table_row.set_bold(True)
    table_row.set_font_color('black')
    table_row.set_font_name('Arial')
    table_row.set_font_size(11)
    table_row.set_bg_color('#cceeff')
    table_row.set_num_format('0.00%')
    return table_row

def workbook_table_row_total(workbook, currency):
    table_row = workbook.add_format()
    table_row.set_bold(True)
    table_row.set_font_color('black')
    table_row.set_font_name('Arial')
    table_row.set_font_size(11)
    table_row.set_bg_color('#cceeff')
    table_row.set_num_format('[$'+currency+'-3409]#,##0.00;[RED](-[$'+currency+'-3409]#,##0.00)')
    table_row.set_top(2)
    return table_row


class HRAttendanceSummary(models.AbstractModel):
    _name = 'report.hrms_attendance_summary.attendance_summary_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, line):
        # One sheet by partner
        summary = workbook.add_worksheet('Summary')
        table_label = workbook_table_label(workbook)
        table_label.set_text_wrap()
        table_label_data = workbook_table_label_data(workbook)
        table_label_data_datetime = table_label_data

        # table_label_data_currency = workbook_table_label_data_currency(workbook, currency)
        table_label_data_datetime.set_num_format('dd/mm/yyyy hh:mm AM/PM')
        table_label_data_date = workbook_table_label_data(workbook)
        table_label_data_date.set_num_format('dd/mm/yyyy')
        table_header = workbook_table_header(workbook)
        table_row_index = workbook_table_row_index(workbook)
        table_row = workbook_table_row(workbook)
        table_row_percent = workbook_table_row_percent(workbook)
        # table_row_total = workbook_table_row_total(workbook, currency)
        format1 = workbook.add_format({'font_size': 18, 'font_name': 'arial','bg_color':'#CFE2F3','bold': 1})
        format1.set_align('center')
        summary.set_row(0, 20)
        summary.set_column(1, 1, 25)
        summary.merge_range('A1:H1', "Employee Attendance Summary", format1)

        headings = ('Day Of Week', 'Schedule', 'Attendance')
        summary.write_row(6, 0, headings, table_label)
        row = 7
        records = []
        for i in line.summary_line_ids:
            records = [i.dayofweek, i.schedule, i.attendance]
            summary.write_row(row, 0, records, table_label_data)
            row += 1
        summary.set_column(1, 1 + len(records), 25)
