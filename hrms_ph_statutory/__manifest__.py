# -*- coding: utf-8 -*-
{
    "name": "HRMS Payroll PH Statutory",
    "summary": "Agilis Localized Payroll BIR Statutory Reports",
    "description": """
Generates the following:
    * BIR 1601c
    * BIR 1604cf
    """,
    "version": "12",
    "author": "Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "category": "Human Resource",
    "depends": [
            'hr',
            'hr_payroll',
            'hrms_payroll_suite',
            'ducument_approval',
            'report_xlsx',
        ],
    "data": [
        'security/ir.model.access.csv',
        'views/bir_1601c.xml',
        'views/employee_annualization.xml',
        'views/salary_rule.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
