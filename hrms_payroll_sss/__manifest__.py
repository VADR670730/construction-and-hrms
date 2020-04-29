# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (https://akretion.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HRMS Social Security System",
    "summary": "Agilis Localized Payroll - SSS",
    "description": """
Salary Rule Formula: result = contract.compute_sss(payslip, current_gross, contribution_type, sss_code, gross_code)

Contribution Type: "EE", "ER", "EC"


Example: result = contract.compute_sss(payslip, categories.GROSS, "EE", "SSSEE", "GROSS")
    """,
    "version": "12",
    "author": "Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "category": "Human Resource",
    "depends": [
        'hr',
        'hr_attendance',
        'hr_payroll',
        'hrms_payroll',
        'ducument_approval',],
    "data": [
        'security/ir.model.access.csv',
        'views/social_security.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
