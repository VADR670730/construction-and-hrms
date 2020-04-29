# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (https://akretion.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HRMS Operation Cutoff",
    "summary": "Agilis Localized Timekeeping - Operation Cutoff",
    "version": "12",
    "author": "Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "category": "Human Resource",
    "depends": [
        'hr',
        'hr_attendance',
        'ducument_approval',],
    "data": [
        'security/ir.model.access.csv',
        'views/operation_cutoff.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
