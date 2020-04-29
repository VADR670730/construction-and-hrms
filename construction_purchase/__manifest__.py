# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015  ADHOC SA  (http://www.adhoc.com.ar)
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'author':  'Dennis Boy Silva - (Agilis Enterprise Solutions Inc.)',
    'website': 'agilis.com.ph',
    'license': 'AGPL-3',
    'category': 'Project',
    'data': [
            'wizard/do_purchase_requisition.xml',
            'wizard/do_create_po.xml',
            'report/purchase_requisition_report.xml',
            'report/purchase_tender_report.xml',
            'report/purchase_order_report.xml',
            'report/material_issuance_slip.xml',
            'views/project.xml',
            'views/invoice.xml',
            'views/purchase.xml',
            'views/stock.xml',
        ],
    'depends': [
            'account',
            'analytic',
            'project',
            'stock',
            'purchase_requisition',
            # 'web_fontawesome',
            'construction_project_management_base',
            'construction_budget',
            'purchase_request',
            'purchase_order_line_menu',
            'construction_boq_and_material_management',
        ],
    'description': '''
Construction Project Purchase Management''',
    'installable': True,
    'auto_install': False,
    'name': "Construction Purchase",
    'summary': 'Construction Project Purchase Management',
    'test': [],
    'version': '12.0.0'

}
