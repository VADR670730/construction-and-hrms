# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015  ADHOC SA  (http://www.adhoc.com.ar)
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'author':  'Agilis Enterprise Solutions Inc.',
    'website': 'agilis-solutions.com',
    'license': 'AGPL-3',
    'category': 'Payroll',
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/deduction.xml',
        ],
    'depends': [
            'hr',
            'hr_contract',
            'hr_payroll',
            'hrms_payroll',
            'ducument_approval',
        ],
    'description': '''
The following Features:
    * Loan and Deduction are deducted on the cutoff Payslip based on the Parameter set.''',
    'installable': True,
    'auto_install': False,
    'name': "Loan/Deduction Management",
    'summary': 'Loan and Deduction are deducted on the cutoff Payslip based on the Parameter set.',
    'test': [],
    'version': '8.0.0'

}
