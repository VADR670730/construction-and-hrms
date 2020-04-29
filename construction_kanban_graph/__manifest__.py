# -*- coding: utf-8 -*-

{
    'author':  'Dennis Boy Silva - Agilis Enterprise Solutions, Inc.',
    'website': 'www.agilis.com.ph',
    'license': 'AGPL-3',
    'version': '11.0.0',
    'category': 'Project',
    'name': "Construction Kanban Graph",
    'summary': 'Construction - Display Project Status in the Kanban',
    'description': '''
        Construction Project Management''',
    'data': [
        'views/project.xml',
        ],
    'depends': [
            'project',
            'construction_project_management_base',
            'web_kanban_graph'
        ],
    'installable': True,
    'auto_install': False,
    'application': True,

}
