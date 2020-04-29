# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
import logging
import itertools
import calendar
from odoo.exceptions import ValidationError
from num2words import num2words
_logger = logging.getLogger("_name_")


class AccountPayment(models.Model):
    _inherit = 'account.payment'

# ==========Cheque Details==========
    cheque_ref = fields.Char(string="Cheque Reference")
    cheque_date = fields.Date(string="Cheque Date")
    bank_ref_id = fields.Many2one('res.partner.bank', string="Bank Reference")
    # bank_id = fields.Many2one('account.journal',
    #                           string="Bank Reference",
    #                           domain=[('type', 'in', ['bank'])])
    cheque_date_rcv = fields.Date(string="Cheque Date Received")
    cheque_date_cleared = fields.Date(string="Cheque Date Cleared")

# ==========Receipt Details==========
    probationary_receipt_no = fields.Char(string="Probationary Receipt Number")
    ack_receipt_no = fields.Char(string="Acknowledgement Receipt Number")
    official_receipt_no = fields.Char(string="Official Receipt Number")

class PartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.multi
    def name_get(self):
        data = []
        for i in self:
            display_value = '{} - {}'.format(i.bank_id.name, i.acc_number)
            data.append((i.id, display_value))
        return data