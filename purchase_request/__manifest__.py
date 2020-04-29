# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Request Purchase Product',
    'version': '12.0',
    'category': 'Purchases',
    'author':'Dennis Boy Silva and tung.tung11191@gmail.com',
    'description': """
Use Purchase Request module for requesting product.
    """,
    'summary': 'Create purchase request',
    'website': 'https://www.odoo.com/page/survey',
    'depends': ['mail',
                 'website',
                 'account',
                 'purchase',
                 'purchase_requisition',
                 'stock',
                 'hr'],
	'images': ['static/description/icon.jpg'],
    'data': [
        'data/purchase_request_data.xml',
        'security/purchase_request_security.xml',
        'security/ir.model.access.csv',
        'wizard/do_purchase_requisition.xml',
        'views/purchase_request_view.xml',
        'views/purchase.xml',
        'views/stock.xml',

    ],
    'depends': ['hr', 'stock','purchase', 'purchase_requisition'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 105,
    'license': 'AGPL-3',
}
