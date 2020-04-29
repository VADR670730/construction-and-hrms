# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (https://akretion.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HRMS Official Business + Overtime",
    "summary": "Agilis Localized Timekeeping - Auto-create Overtime request if Official Business falls to Restdays schedule.",
    "version": "12",
    "author": "Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "category": "Human Resource",
    "depends": [
        'hr',
        'hr_attendance',
        'hrms_official_business',
        'ducument_approval',
        'hrms_work_schedule',
        'hrms_overtime',],
    "data": [
        'views/official_business_overtime.xml'
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
