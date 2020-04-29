# -*- coding: utf-8 -*-
from odoo import http

# class ../custom/addons/checkVoucher(http.Controller):
#     @http.route('/../custom/addons/check_voucher/../custom/addons/check_voucher/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/../custom/addons/check_voucher/../custom/addons/check_voucher/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('../custom/addons/check_voucher.listing', {
#             'root': '/../custom/addons/check_voucher/../custom/addons/check_voucher',
#             'objects': http.request.env['../custom/addons/check_voucher.../custom/addons/check_voucher'].search([]),
#         })

#     @http.route('/../custom/addons/check_voucher/../custom/addons/check_voucher/objects/<model("../custom/addons/check_voucher.../custom/addons/check_voucher"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('../custom/addons/check_voucher.object', {
#             'object': obj
#         })