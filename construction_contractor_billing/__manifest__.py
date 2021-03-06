# -*- coding: utf-8 -*-
{
    'name': "Construction Contractors Billing",
    'summary': """Construction Contractors Billing""",
    'description': """

    """,
    'author': "Dennis Boy Silva - Agilis Enterprise Solutions, Inc.",
    'website': "http://www.agilis.com.ph",
    'category': 'Project',
    'version': '12.1',
    # any module necessary for this one to work correctly
    'depends': [
        'project',
        'stock',
        'construction_project_management_base',
        'construction_budget',
        'construction_visual_inspection',
        'ducument_approval',
        'construction_boq_and_material_management',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/billing_data.xml',
        'views/contractor_billing.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    'auto_install': False,
}
