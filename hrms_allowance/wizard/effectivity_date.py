# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date,datetime


class EffectivityDateAllowance(models.TransientModel):
    _name = "effectivity.date.wizard"

    effectivity_date = fields.Date(string='Effectivity Date', required=True, default=date.today())

    @api.multi
    def submit_date(self):
        allowance = self.env['hr.allowance'].browse(self._context.get('active_id'))
        allowance.write({
            'effectivity_date': self.effectivity_date,
            'state': 'approved',
            'approved_by': self._uid,
            'approved_date': datetime.now()})
        return {'type': 'ir.actions.act_window_close'}
