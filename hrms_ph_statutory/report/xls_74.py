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


class HRMSAnnualization74(models.AbstractModel):
    _name = 'report.hrms_ph_statutory.annualization74'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, line):
        title = workbook_title(workbook)
        header = workbook_header(workbook)
        data_name = workbook_data_names(workbook)
        data_number = workbook_data_numbers(workbook)
        worksheet = workbook.add_worksheet("Schedule 7.4")
        worksheet.set_row(4, 30)
        worksheet.set_column('B1:AH1', 30)
        worksheet.set_column('AH1:AI1', 15)
        worksheet.merge_range('A1:AI1', 'ALPHALIST OF EMPLOYEES AS OF DECEMBER 31 WITH PREVIOUS EMPLOYER/S WITHIN THE YEAR (Reported Under BIR Form No. 2316)', title)
        worksheet.merge_range("A2:A5", "SEQ NO",header)
        worksheet.merge_range("B2:B5", "TIN",header)
        worksheet.merge_range("C2:E3", "NAME OF EMPLOYEES",header)
        worksheet.merge_range("C4:C5", "Last Name",header)
        worksheet.merge_range("D4:D5", "First Name",header)
        worksheet.merge_range("E4:E5", "Middle Name",header)
        worksheet.merge_range("F2:AB2", "GROSS COMPENSATION INCOME",header)
        worksheet.merge_range("F3:F5", "GROSS COMPENSATION INCOME",header)
        worksheet.merge_range("G3:O3", "PREVIOUS EMPLOYER",header)
        worksheet.merge_range("G4:K4", "NON-TAXABLE",header)
        worksheet.write("G5", "13th Month Pay & Other Benefits", header)
        worksheet.write("H5", "De Minimis Benefits", header)
        worksheet.write("I5", "SSS,GSIS,PHIC, & Pag - ibig Constributions, and Union Dues", header)
        worksheet.write("J5", "Salaries and Other Form of Compensations", header)
        worksheet.write("K5", "Total Non-Taxable/Exempt Compensation Income", header)
        worksheet.merge_range("L4:O4", "TAXABLE",header)
        worksheet.write("L5", "Basic Salary", header)
        worksheet.write("M5", "13th Month Pay & Other Benefits", header)
        worksheet.write("N5", "Salaries and Other Form of Compensations", header)
        worksheet.write("O5", "Total Taxable", header)
        worksheet.merge_range("P3:W3", "PRESENT EMPLOYER",header)
        worksheet.merge_range("P4:T4", "NON-TAXABLE",header)
        worksheet.write("P5", "13th Month Pay & Other Benefits", header)
        worksheet.write("Q5", "De Minimis Benefits", header)
        worksheet.write("R5", "SSS,GSIS,PHIC, & Pag - ibig Constributions, and Union Dues", header)
        worksheet.write("S5", "Salaries and Other Form of Compensations", header)
        worksheet.write("T5", "Total Non-Taxable/Exempt Compensation Income", header)
        worksheet.merge_range("U4:W4", "TAXABLE", header)
        worksheet.write("U5", "Basic Salary", header)
        worksheet.write("V5", "13th Month Pay & Other Benefits", header)
        worksheet.write("W5", "Salaries and Other Form of Compensations", header)
        worksheet.merge_range("X3:X5", "Total Compensation Present",header)
        worksheet.merge_range("Y3:Y5", "Total Taxable \n(Previous and Present Employer)",header)
        worksheet.merge_range("Z3:AA4", "EXEMPTION", header)
        worksheet.write("Z5", "Code", header)
        worksheet.write("AA5", "Amount", header)
        worksheet.merge_range("AB3:AB5", "Premium Paid on Health and/or Hospital Insurance",header)
        worksheet.merge_range("AC2:AC5", "Net Taxable Compensation Income",header)
        worksheet.merge_range("AD2:AD5", "Tax Due",header)
        worksheet.merge_range("AE2:AF3", "Tax Withheld",header)
        worksheet.merge_range("AE4:AE5", "PREVIOUS EMPLOYER",header)
        worksheet.merge_range("AF4:AF5", "PRESENT EMPLOYER",header)
        worksheet.merge_range("AG2:AH3", "YEAR END ADJUSTMENT",header)
        worksheet.merge_range("AG4:AG5", "Amount Withheld and Paid for in December ", header)
        worksheet.merge_range("AH4:AH5", "Over Withheld Tax Refunded to Employee", header)
        worksheet.merge_range("AI2:AI5", "Amount of Tax Withheld as Adjusted",header)
