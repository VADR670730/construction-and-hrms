# -*- coding: utf-8 -*-

{
    'author':  'Srikesh Infotech',
    'website': 'www.srikeshinfotech.com',
    'license': 'AGPL-3',
    'version': '11.0.0',
    'category': 'Project',
    'name': "Construction BOQ and Material Management",
    'summary': 'Construction Project Management customized module',
    'description': '''
        Construction Project Management''',
    'data': [
        'security/ir.model.access.csv',
        'views/project_boq.xml',
        'views/project.xml',
        'wizard/project_wizard.xml',
        'views/project_task.xml',
        'views/task.xml',
        'views/material_req.xml',
        'views/project_eco.xml',
        ],
    'depends': [
            'project',
            'construction_project_management_base',
            'hr',
            'web_kanban_graph'
        ],
    'installable': True,
    'auto_install': False,
    'application': False,

}
