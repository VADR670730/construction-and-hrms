# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (https://akretion.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HRMS Payroll - Leave Convertion",
    "summary": "Agilis Payroll Leave Convertion and Other parameters",
    "version": "12",
    "author": "Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "category": "Human Resource",
    "depends": [
        'hr',
        'hr_payroll',
        'hr_contract',
        'hr_holidays',
        'hrms_payroll'
        ],
    "data": [
        'security/ir.model.access.csv',
        'views/leave.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
