# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (https://akretion.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HRMS Attendance Summary",
    "summary": "Agilis Localized Timekeeping -Attendance Summary",
    "version": "12",
    "author": "Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "category": "Human Resource",
    "depends": [
        'hr',
        'hr_attendance',
        'hrms_official_business',
        'ducument_approval',
        'hrms_work_schedule',
        'hrms_company_holiday',
        'hrms_overtime',
        'hrms_official_business',
        'hrms_official_business_overtime',
        'hrms_operation_cutoff',
        'hrms_shift_overtime',
        'hrms_shifting_schedule',
        'hrms_undertime_request',
        'report_xlsx',
        'hrms_cutoff_template',
    ],
    "data": [
        'security/ir.model.access.csv',
        'report/attendance_summary.xml',
        'wizard/emloyee_attendance.xml',
        'views/attendance_summary.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
