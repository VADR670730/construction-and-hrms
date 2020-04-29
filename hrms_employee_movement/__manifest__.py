# coding: utf-8
{
    'name': "HRMS Employee Movement",

    'summary': """
        Part of HRMS V3 Application""",

    'description': """
        Employee Movement Module allows to track the Empoyee movement within the company
    """,

    'author': "John Ardosa, Raymund Martinez, and Ralf Cabarogias - Agilis Enterprise Solutions",
    'website': "http://www.yourcompany.com",

    'category': 'HR',
    'version': '0.1',

    'depends': [
        'base',
        'hr',
        'hrms_employee_201'
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/employee_movement.xml',

    ],
}
