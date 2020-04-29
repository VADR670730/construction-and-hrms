# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (https://akretion.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HRMS Company Holiday",
    "summary": "Agilis Localized Timekeeping - Company Holiday",
    "version": "12",
    "author": "Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "category": "Human Resource",
    "depends": ['hr', 'hr_attendance'],
    "data": [
        'security/ir.model.access.csv',
        'views/company_holiday.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
