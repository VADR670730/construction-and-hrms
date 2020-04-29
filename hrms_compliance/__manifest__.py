# coding: utf-8
{
    'name': "HRMS Compliance",

    'summary': """
        This module focuses on Infraction Management and Workplace Accidents""",

    'description': """
        Long description of module's purpose
    """,

    'author': "John Christian Ardosa, Raymund MARTINEZ, Ralf Cabarogias – Agilis Enterprise Solutions Inc.",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': [
        'base',
        'contacts',
        'hr',
        'hrms_employee_201',
        'mail',
    ],

    'data': [
        'security/ir.model.access.csv',
        # 'security/security.xml',    
        'wizard/suspension.xml',
        'views/infraction.xml',
        'views/policy.xml',
        'views/offense.xml',
        'views/violation.xml',
        'views/action_history.xml',
        # 'views/create_suspension.xml',
        'views/suspension_history.xml',
        'data/sequence.xml',
        'data/mail_template.xml',
        'views/menu_views.xml',

    ],
    'demo': [
        'demo/demo.xml',
    ],

    "license": "AGPL-3",
    "installable": True,
    "application": False,
    'auto_install': False,
}
