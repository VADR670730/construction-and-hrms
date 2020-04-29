# -*- coding: utf-8 -*-
{
    'name': "Check Voucher - Agilis Enterprise Solutions",

    'summary': """
        Transforming Physical Check Voucher Forms into Electronic.""",

    'description': """
        This module's purpose is to make an electronic Check Voucher 
        that is linked to invoices and purchases for invoice numbers and bills
        and contacts and HR for preparation, certification, approval, and receipt
    """,

    'author': "John Christian Ardosa(Agilis Enterprise Solutions)",
    'website': "http://agilis.com.ph",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_check_printing', 'account','account_accountant', 'hr', 'contacts', 'purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'security/security.xml',
        'views/check_voucher_view.xml',
        'views/particulars_view.xml',
        'views/account_distribution.xml',
        'views/account_views_inherit.xml',
        'data/sequence.xml',
        'reports/report.xml',
        'reports/check_voucher.xml',
        'reports/check_voucher_v2.xml',
        # 'reports/check_voucher_v3.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'auto_install': False,
    'css': ['static/src/css/check_voucher.css'],
}
