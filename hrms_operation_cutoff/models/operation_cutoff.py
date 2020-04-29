# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from datetime import date, datetime, timedelta, time

class HROperationCutoff(models.Model):
    _name = 'hr.operation.cutoff'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin', 'document.default.approval']

    def _get_default_companies(self):
        companies = [rec.id for rec in self.env['res.company'].search([('id', 'child_of', [self.env.user.company_id.id])])]
        return companies

    name = fields.Char(string="Title", required=True, track_visibility="always")
    memorandum = fields.Binary(string="Memorandum", track_visibility="always")
    company_ids = fields.Many2many('res.company', 'cotoff_company_rel', string="Company/Branch Affected",
                                   required=True, default=_get_default_companies, track_visibility="always")
    start_date = fields.Datetime(string="Start Date", required=True, track_visibility="always")
    end_date = fields.Datetime(string="End Date", required=True, track_visibility="always")

    @api.multi
    def add_follower(self):
        partner_ids = []
        for employee in self.env['hr.employee'].search([('company_id', 'in', [i.id for i in self.company_ids])]):
            if employee.parent_id and employee.parent_id.user_id:
                partner_ids.append(employee.parent_id.user_id.partner_id.id)
            if employee.user_id:
                partner_ids.append(employee.user_id.partner_id.id)
        if partner_ids:
            self.message_subscribe(partner_ids=partner_ids)

    @api.multi
    def approve_request(self):
        res = super(HROperationCutoff, self).approve_request()
        self.add_follower()
        msg_body = """
            This is to inform you that we will hava a
            Company Oparation Cutoff starting from %s to %s.
        """%(self.start_date.strftime(DT), self.end_date.strftime(DT))
        self.message_post(body=msg_body,subject="Operatio Cutoff - Approved")
        return res
