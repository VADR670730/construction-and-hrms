# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (https://akretion.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HRMS Upload Attendance",
    "summary": "Agilis Localized Timekeeping - Upload attendance CSV files from biometric",
    "version": "12",
    "author": "Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "category": "Human Resource",
    "depends": [
        'hr',
        'hr_attendance',],
    "data": [
        'security/ir.model.access.csv',
        'views/attendance.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
