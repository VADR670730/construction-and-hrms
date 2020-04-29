# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (https://akretion.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HRMS Cutoff Template",
    "summary": "Agilis Cutoff Template",
    "version": "12",
    "author": "Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "category": "Human Resource",
    "depends": [
        'hr',
        'hr_contract',],
    "data": [
        'security/ir.model.access.csv',
        'views/contract.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
