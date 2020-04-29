# -*- coding: utf-8 -*-

{
    'author':  'Dennis Boy Silva - Agilis Enterprise Solutions Inc.',
    'website': 'agilis-solutions.com',
    # 'license': 'AGPL-3',
    'category': 'Payroll',
    'data': [
        'security/ir.model.access.csv',
        'views/payslip.xml',
        ],
    'depends': [
            'hr',
            'hr_contract',
            'hr_payroll',
            'ducument_approval',
            'hrms_payroll',
            'hrms_deduction',
        ],
    'description': '''
Computes Final Payment base PH DOLE''',
    'installable': True,
    'auto_install': False,
    'name': "HRMS Payroll - Final Payment",
    'summary': 'Computes Final Payment base PH DOLE',
    'test': [],
    'version': '8.0.0'

}
