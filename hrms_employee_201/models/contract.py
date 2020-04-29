# coding: utf-8
from odoo import models, fields, api
from datetime import date
import logging

_logger = logging.getLogger("_name_")


class HRMSContract(models.Model):
    _inherit = 'hr.contract'

    date_created = fields.Date("Date Created")
    reason_changing = fields.Char("Reason For Changing")

    @api.model
    def create(self, vals):
        res = super(HRMSContract, self).create(vals)
        for rec in res:
            rec.date_created = date.today()
        return res
