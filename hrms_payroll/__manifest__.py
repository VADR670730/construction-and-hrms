# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (https://akretion.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HRMS Payroll Report",
    "summary": "Agilis Payroll Reports",
    "version": "12",
    "author": "Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "category": "Human Resource",
    "depends": [
        'hr',
        'hr_payroll',
        'hr_contract',
        'report_xlsx',
        'hrms_cutoff_template'],
    "data": [
        'security/ir.model.access.csv',
        'report/payroll_register_xls.xml',
        'wizard/process_report.xml',
        'wizard/create_payslip_batch.xml',
        'views/payslip.xml',
        # 'views/contract.xml',
        'views/wtax.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
