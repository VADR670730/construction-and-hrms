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


class HRMSAnnualization73(models.AbstractModel):
    _name = 'report.hrms_ph_statutory.annualization73'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, line):
        title = workbook_title(workbook)
        header = workbook_header(workbook)
        data_name = workbook_data_names(workbook)
        data_number = workbook_data_numbers(workbook)
        worksheet = workbook.add_worksheet("Schedule 7.3")
        worksheet.set_row(3, 30)
        worksheet.set_column('B1:Y1', 30)
        worksheet.set_column('Z1:Z1', 15)
        worksheet.merge_range('A1:AA1', 'ALPHALIST OF EMPLOYEES AS OF DECEMBER 31 WITH NO PREVIOUS EMPLOYER WITHIN THE YEAR (Reported Under BIR Form No.2316)', title)
        worksheet.merge_range('A2:A4', "SEQ NO",header)
        worksheet.merge_range("B2:B4", "TIN",header)
        worksheet.merge_range("C2:E2", "NAME OF EMPLOYEES",header)
        worksheet.merge_range("C3:C4", "Last Name",header)
        worksheet.merge_range("D3:D4", "First Name",header)
        worksheet.merge_range("E3:E4", "Middle Name",header)
        worksheet.merge_range("F2:O2", "GROSS COMPENSATION INCOME",header)
        worksheet.merge_range("F3:F4", "Gross Compensation Income",header)
        worksheet.merge_range("G3:K3", "NON-TAXABLE",header)
        worksheet.write("G4", "13th Month Pay & Other Benefits", header)
        worksheet.write("H4", "De Minimis Benefits", header)
        worksheet.write("I4", "SSS,GSIS,PHIC, & Pag - ibig Constributions, and Union Dues", header)
        worksheet.write("J4", "Salaries and Other Form of Compensations", header)
        worksheet.write("K4", "Total Non-Taxable/Exempt Compensation Income", header)
        worksheet.merge_range("L3:O3", "TAXABLE",header)
        worksheet.write("L4", "Basic Salary", header)
        worksheet.write("M4", "13th Month Pay & Other Benefits", header)
        worksheet.write("N4", "Salaries and Other Form of Compensations", header)
        worksheet.write("O4", "Total Taxable/Exempt Compensation Income", header)
        worksheet.merge_range("P2:Q3", "EXEMPTION",header)
        worksheet.write("P4", "Code", header)
        worksheet.write("Q4", "Amount", header)
        worksheet.merge_range("R2:R4", "Premium Paid on Health and,or Hospital Insurance",header)
        worksheet.merge_range("S2:S4", "Net Taxable Compensation Income",header)
        worksheet.merge_range("T2:T4", "Tax Due",header)
        worksheet.merge_range("U2:U4", "Tax Withheld",header)
        worksheet.merge_range("V2:V4", "YEAR END ADJUSTMENT",header)
        worksheet.merge_range("W2:W4", "Amount Withheld and Paid for in December ", header)
        worksheet.merge_range("X2:X4", "Over Withheld Tax Refunded to Employee", header)
        worksheet.merge_range("Y2:Y4", "Amount of Tax Withheld as Adjusted",header)
        worksheet.merge_range("Z2:Z4", "Substituted Filling? Yes/No",header)
