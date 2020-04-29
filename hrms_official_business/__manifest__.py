# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (https://akretion.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HRMS Official Business",
    "summary": "Agilis Localized Timekeeping - Official Business",
    "version": "12",
    "author": "Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "category": "Human Resource",
    "depends": [
        'hr',
        'hr_attendance',
        'ducument_approval',
        'hrms_company_holiday',
        'hrms_work_schedule'],
    "data": [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/official_business.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
