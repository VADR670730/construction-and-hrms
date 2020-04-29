# -*- coding: utf-8 -*-
'''
Created on 7th of Feb 2020
@author: Dennis
'''

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger("_name_")

def workbook_title(workbook):
    format = workbook.add_format()
    format.set_font_color('black')
    format.set_font_name('Arial')
    format.set_font_size(14)
    format.set_bold(True)
    format.set_align('left')
    format.set_align('vcenter')
    return format

def workbook_header(workbook):
    format = workbook.add_format()
    format.set_font_color('black')
    format.set_font_name('Arial')
    format.set_font_size(12)
    format.set_bold(True)
    format.set_align('center')
    format.set_align('vcenter')
    format.set_text_wrap()
    return format

def workbook_data_names(workbook):
    format = workbook.add_format()
    format.set_font_color('black')
    format.set_font_name('Arial')
    format.set_font_size(10)
    format.set_align('left')
    return format

def workbook_data_numbers(workbook):
    format= workbook.add_format()
    format.set_font_color('black')
    format.set_font_name('Arial')
    format.set_font_size(10)
    format.set_align('right')
    return format


class HRMSAnnualization75(models.AbstractModel):
    _name = 'report.hrms_ph_statutory.annualization75'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, line):
        title = workbook_title(workbook)
        header = workbook_header(workbook)
        data_name = workbook_data_names(workbook)
        data_number = workbook_data_numbers(workbook)
        worksheet = workbook.add_worksheet("Schedule 7.5")
        worksheet.set_row(5, 30)
        worksheet.set_column('B1:AH1', 30)
        worksheet.set_column('AH1:AI1', 15)
        worksheet.merge_range('A1:AI1', 'ALPHALIST OF MINIMUM WAGE EARNERS (Reported Under BIR Form No. 2316)', title)
        worksheet.merge_range("A2:A56", "SEQ NO",header)
        worksheet.merge_range("B2:B6", "TIN",header)
        worksheet.merge_range("C2:E3", "NAME OF EMPLOYEES",header)
        worksheet.merge_range("C4:C6", "Last Name",header)
        worksheet.merge_range("D4:D6", "First Name",header)
        worksheet.merge_range("E4:E6", "Middle Name",header)
        worksheet.merge_range("F2:F6", "Region No. Where Assigned",header)
        worksheet.merge_range("G2:AA2", "GROSS COMPENSATION INCOME",header)
        worksheet.merge_range("G3:T3", "PREVIOUS EMPLOYER",header)
        worksheet.merge_range("G4:Q4", "NON-TAXABLE",header)

        worksheet.merge_range("G5:G6", "Gross Compensation Income \nPrevious", header)
        worksheet.merge_range("H5:H6", "Basic /SMW", header)
        worksheet.merge_range("I5:I6", "Holiday Pay", header)
        worksheet.merge_range("J5:J6", "Overtime Pay", header)
        worksheet.merge_range("K5:K6", "Night Shift Differential", header)
        worksheet.merge_range("L5:L6", "Hazard Pay", header)
        worksheet.merge_range("M5:M6", "13th month and Other Benefits", header)
        worksheet.merge_range("N5:N6", "De Minimis Benefits", header)
        worksheet.merge_range("O5:O6", "SSS, GSIS, PHIC and Pag-ibig Contribution, and Union Dues", header)
        worksheet.merge_range("P5:P6", "Salaries and Other form of Contributions", header)
        worksheet.merge_range("Q5:Q6", "Total Non-taxable/Excempt Compensation Income", header)

        worksheet.merge_range("R4:T4", "TAXABLE", header)
        worksheet.merge_range("R5:R6", "13th month and Other Benefits", header)
        worksheet.merge_range("S5:S6", "Salaries and Other form of Contributions", header)
        worksheet.merge_range("T5:T6", "Total Taxable", header)
        worksheet.merge_range("U3:AK3", "PRESENT EMPLOYER",header)
        worksheet.merge_range(3, 3, 20, 34, "NON-TAXABLE",header)
        worksheet.write(4, 20, "Date From", header)
        worksheet.write(4, 21, "Date To", header)
        worksheet.write(4, 22, "Gross Compensation Income - Previous", header)
        worksheet.write(4, 23, "Basic SMW \n(Per Day)", header)
        worksheet.write(4, 24, "Basic SMW \n(Per Month)", header)
        worksheet.write(4, 25, "Basic SMW \n(Per Year)", header)
        worksheet.write(4, 26, "Factor Used", header)
        worksheet.write(4, 27, "Holiday Pay", header)
        worksheet.write(4, 28, "Overtime Pay", header)
        worksheet.write(4, 29, "Night Shift Differential", header)
        worksheet.write(4, 30, "Hazard Pay", header)
        worksheet.write(4, 31, "13th month and Other Benefits", header)
        worksheet.write(4, 32, "De Minimis Benefits", header)
        worksheet.write(4, 33, "SSS, GSIS, PHIC and Pag-ibig Contribution, and Union Dues", header)
        worksheet.write(4, 34, "Salaries and Other form of Contributions", header)
        worksheet.merge_range(3, 3, 35, 36, "TAXABLE",header)
        worksheet.write(4, 35, "13th month and Other Benefits", header)
        worksheet.write(4, 36, "Salaries and Other form of Contributions", header)
        worksheet.merge_range(2, 4, 37, 37, "Total Compensation - Present",header)
        worksheet.merge_range(1, 4, 38, 38, "Total Compensation Income - Previous & Present",header)
        worksheet.merge_range(1, 3, 39, 40, "EXEMPTION",header)
        worksheet.write(4, 39, "Code", header)
        worksheet.write(4, 40, "Amount", header)
        worksheet.merge_range(1, 4, 41, 41, "Premium Paid on Health and/or Hospital Insurance",header)
        worksheet.merge_range(1, 4, 42, 42, "Net Taxable Compensation Income",header)
        worksheet.merge_range(1, 4, 43, 43, "Tax Due",header)
        worksheet.merge_range(1, 2, 44, 45, "Tax Withheld",header)
        worksheet.merge_range(3, 4, 44, 44, "PREVIOUS EMPLOYER",header)
        worksheet.merge_range(3, 4, 45, 45, "PRESENT EMPLOYER",header)
        worksheet.merge_range(1, 3, 46, 47, "YEAR END ADJUSTMENT",header)
        worksheet.write(4, 46, "Amount Withheld and Paid for in December ", header)
        worksheet.write(4, 47, "Over Withheld Tax Refunded to Employee", header)
        worksheet.merge_range(1, 4, 48, 48, "Amount of Tax Withheld as Adjusted",header)
