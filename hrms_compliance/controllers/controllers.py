# -*- coding: utf-8 -*-
from odoo import http

# class Hrv3Compliance(http.Controller):
#     @http.route('/hrv3_compliance/hrv3_compliance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hrv3_compliance/hrv3_compliance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hrv3_compliance.listing', {
#             'root': '/hrv3_compliance/hrv3_compliance',
#             'objects': http.request.env['hrv3_compliance.hrv3_compliance'].search([]),
#         })

#     @http.route('/hrv3_compliance/hrv3_compliance/objects/<model("hrv3_compliance.hrv3_compliance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hrv3_compliance.object', {
#             'object': obj
#         })