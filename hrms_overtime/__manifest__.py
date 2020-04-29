# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (https://akretion.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HRMS Overtime",
    "summary": "Agilis Localized Timekeeping - Overtime Management",
    "version": "12",
    "author": "Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "category": "Human Resource",
    "depends": [
        'hr',
        'hr_attendance',
        'hr_payroll',
        'ducument_approval',
        'hrms_company_holiday',
        'hrms_work_schedule'],
    "data": [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/res_config_setting.xml',
        'views/overtime_type.xml',
        'views/overtime.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
