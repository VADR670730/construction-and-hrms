# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (https://akretion.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HRMS Philhealth",
    "summary": "Agilis Localized Payroll - Philhealth",
    "description": """
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
        'views/philhealth.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
