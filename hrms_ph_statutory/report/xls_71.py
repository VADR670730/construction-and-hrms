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


class HRMSAnnualization71(models.AbstractModel):
    _name = 'report.hrms_ph_statutory.annualization71'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, line):
        title = workbook_title(workbook)
        header = workbook_header(workbook)
        data_name = workbook_data_names(workbook)
        data_number = workbook_data_numbers(workbook)
        worksheet = workbook.add_worksheet("Schedule 7.1")
        worksheet.set_row(3, 30)
        worksheet.set_column('B1:Z1', 30)
        worksheet.set_column('AA1:AA1', 15)
        worksheet.merge_range('A1:AA1', 'ALPHALIST OF EMPLOYEES TERMINATED BEFORE DECEMBER 31 (Reported Under BIR Form No. 2316)', title)
        worksheet.merge_range('A2:A4', "SEQ NO",header)
        worksheet.merge_range("B2:B4", "TIN",header)
        worksheet.merge_range("C2:E2", "NAME OF EMPLOYEES",header)
        worksheet.merge_range("C3:C4", "Last Name",header)
        worksheet.merge_range("D3:D4", "First Name",header)
        worksheet.merge_range("E3:E4", "Middle Name",header)
        worksheet.merge_range("F2:F4", "START DATE",header)
        worksheet.merge_range("G2:G4", "END DATE",header)
        worksheet.merge_range("H2:Q2", "GROSS COMPENSATION INCOME",header)
        worksheet.merge_range("H3:H4", "Gross Compensation Income",header)
        worksheet.merge_range("I3:M3", "NON-TAXABLE",header)
        worksheet.write("I4", "13th Month Pay & Other Benefits", header)
        worksheet.write("J4", "De Minimis Benefits", header)
        worksheet.write("K4", "SSS,GSIS,PHIC, & Pag - ibig Constributions, and Union Dues", header)
        worksheet.write("L4", "Salaries and Other Form of Compensations", header)
        worksheet.write("M4", "Total Non-Taxable/Exempt Compensation Income", header)
        worksheet.merge_range("N3:Q3", "TAXABLE",header)
        worksheet.write("N4", "Basic Salary", header)
        worksheet.write("O4", "13th Month Pay & Other Benefits", header)
        worksheet.write("P4", "Salaries and Other Form of Compensations", header)
        worksheet.write("Q4", "Total Taxable/Exempt Compensation Income", header)
        worksheet.merge_range("R2:S3", "EXEMPTION",header)
        worksheet.write("R4", "Code", header)
        worksheet.write("S4", "Amount", header)
        worksheet.merge_range("T2:T4", "Premium Paid on Health and,or Hospital Insurance",header)
        worksheet.merge_range("U2:U4", "Net Taxable Compensation Income",header)
        worksheet.merge_range("V2:V4", "Tax Due",header)
        worksheet.merge_range("W2:W4", "Tax Withheld",header)
        worksheet.merge_range("X2:Y2", "YEAR END ADJUSTMENT",header)
        worksheet.merge_range("X3:X4", "Amount Withheld and Paid for in December ", header)
        worksheet.merge_range("Y3:Y4", "Over Withheld Tax Refunded to Employee", header)
        worksheet.merge_range("Z2:Z4", "Amount of Tax Withheld as Adjusted",header)
        worksheet.merge_range("AA2:AA4", "Substituted Filling? Yes/No",header)
