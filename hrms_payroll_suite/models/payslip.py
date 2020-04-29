# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def create(self, vals):
        if not vals.get('payslip_run_id'):
            contract = self.env['hr.contract'].browse(vals.get('contract_id'))
            vals['payslip_run_id'] = self.env['hr.payslip.run'].create({
                    'name': vals.get('name'),
                    'date_start': vals.get('date_from'),
                    'date_end': vals.get('date_to'),
                    'month_year': vals.get('payslip_period'),
                    'cutoff_template_id': contract.cutoff_template_id.id,
                    'compute_thirtheenth_month': vals.get('compute_thirtheenth_month'),
                    'cutoff': vals.get('cutoff'),
                    'convert_leave': vals.get('convert_leave')
                    }).id
        return super(HRPayslip, self).create(vals)
