# coding: utf-8
{
    'name': "HRMS Work History",

    'summary': """
        HRMS Work History""",

    'description': """
        Work module module is part of employee 201
    """,

    'author': "John Ardosa, Raymund Martinez, and Ralf Cabarogias - Agilis Enterprise Solutions",
    'website': "http://www.yourcompany.com",

    'category': 'HR',
    'version': '0.1',

    'depends': [
        'base',
        'hr',
        'hrms_employee_201',
        'hrms_recruitment'
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/work_history.xml',

    ],
}
