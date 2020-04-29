# -*- coding: utf-8 -*-

{
    'name': "Construction Visual Management",
    'version': '11.0.0',
    'license': 'AGPL-3',
    'author':  'Srikesh Infotech',
    'website': 'www.srikeshinfotech.com',
    'category': 'Project',
    'description': '''
        Visual Inspection module''',
    'summary': 'Visual Inspection Management',
    'data': [
        'security/ir.model.access.csv',
        'views/visual_inspection.xml',
        ],
    'depends': [
            'project',
            'stock',
        ],
    'installable': True,
    'auto_install': False,

}
