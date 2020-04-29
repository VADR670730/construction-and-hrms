# -*- coding: utf-8 -*-
{
    "name": "HRMS Payroll Suite",
    "summary": "Agilis Localized Payroll Suite",
    "description": """
Manages the following:
    * Payroll Generation and Reports
    * Allowance Allocations
    * Loans and Deductions
    * Final Payment Computations
    * Statutory Contributions
    * Cutoff Management
    * Leave Convertions and 13th month payout
    """,
    "version": "12",
    "author": "Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "category": "Human Resource",
    "depends": [
            'hr',
            'hr_attendance',
            'hr_payroll',
            'hrms_payroll',
            'hrms_payroll_final_payment',
            'hrms_allowance',
            'hrms_deduction',
            'hrms_payroll_pagibig',
            'hrms_payroll_sss',
            'hrms_payroll_philhealth',
            'hrms_payroll_exclude_include',
            'hrms_payroll_leave',
        ],
    "data": [
        # 'security/ir.model.access.csv',
        'views/payroll.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
