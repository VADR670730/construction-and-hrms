# -*- coding: utf-8 -*-

{
    'author':  'Dennis Boy Silva - Agilis Enterprise Solutions Inc.',
    'website': 'agilis-solutions.com',
    # 'license': 'AGPL-3',
    'category': 'Payroll',
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/allowance_view.xml',
        'wizard/effectivity_date_wizard.xml',
        ],
    'depends': [
            'hr',
            'hr_contract',
            'hr_payroll',
            'ducument_approval',
        ],
    'description': '''
The following Features:
    * Fixed Allowances
    * Single Cutoff Allowances
    * Reccuring Allowances''',
    'installable': True,
    'auto_install': False,
    'name': "Allowance Management",
    'summary': 'Allowances are given on the cutoff Payslip based on the Parameter set.',
    'test': [],
    'version': '8.0.0'

}
