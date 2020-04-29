# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class CompanyHoliday(models.Model):
    _name = 'company.holiday'

    def _get_default_companies(self):
        company = [rec.id for rec in self.env['res.company'].search([('id', 'child_of', [self.env.user.company_id.id])])]
        return company


    name = fields.Char(string="Title", required=True)
    date = fields.Date(string="Date", required=True)
    memorandum = fields.Binary(string="Memorandum")
    holiday_type = fields.Selection([
                            ('Regular', 'Regular'),
                            ('Special', 'Special')
                        ], string="Type", required=True, default='Regular')
    company_ids = fields.Many2many('res.company', 'holiday_company_rel', string="Company/Branch Affected",
                                   required=True, default=_get_default_companies)
    company_str = fields.Text(compute='_get_company_data')

    @api.multi
    def _get_company_data(self):
        for i in self:
            company = ''
            for rec in i.company_ids:
                company += '%s,  \n'%(rec.name)
            i.company_str = company
