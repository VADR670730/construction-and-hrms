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


class CheckVoucher(models.Model):
    _name = "check.voucher"
    _description = 'Model used for creating Check Vouchers'
    _rec_name = 'voucher_id_seq'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']

    STATUS = [
        ('draft', 'Draft'),
        ('submitted', 'Waiting for Confirmation'),
        ('confirmed', 'Waiting for Verification'),
        ('verified', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('canceled', 'Canceled')
    ]

    @api.multi
    def _get_date(self):
        return date.today()

    company_id = fields.Many2one('res.company', string='Company Name')

    partner_id = fields.Many2one('res.partner',
                                 string="Payee",
                                 related='payment_id.partner_id',
                                 ondelete='cascade')

    partner_bank_account_id = fields.Many2one('res.partner.bank',
                                              string='Payee Bank Account',
                                              domain="[('bank_id', '=', partner_bank_id),('partner_id','=',partner_id)]"
                                              )

    @api.onchange('partner_id', 'payment_id', 'partner_bank_account_id')
    def _get_bank_name(self):
        h = self.env['res.bank'].search([('name', 'in', [
                                        i.bank_id.name for i in self.env['res.partner.bank'].search([('partner_id', '=', self.partner_id.id)])])])
        bank_name_lines = [i.name for i in h]
        return {'domain': {'partner_bank_id': [('name', 'in', bank_name_lines)]}}

    @api.onchange('partner_bank_id')
    def _return_blank_acct_number(self):
        for i in self:
            i.partner_bank_account_id = False

    partner_bank_id = fields.Many2one('res.bank',
                                      string="Bank",
                                      )

    payment_id = fields.Many2one('account.payment',
                                 string="Payment Reference",
                                 required=True,
                                 domain="[('check_voucher_id', '=', False)]",
                                 )

    voucher_id_seq = fields.Char(string="Voucher No.",
                                 required=True,
                                 copy=False,
                                 readonly=True,
                                 index=True,
                                 default=lambda self: _('New'))

    date = fields.Date(string="Date", default=_get_date)

    @api.onchange('payment_id')
    def _get_bank_id(self):
        for i in self:
            i.bank_id = i.payment_id.journal_id

    bank_id = fields.Many2one('account.journal',
                              string="Bank",
                              domain=[('type', 'in', ['bank'])],
                              )
    bank_account_no = fields.Char(string="Account No.",
                                  related='bank_id.bank_account_id.acc_number',
                                  readonly=True,
                                  store=True
                                  )
    check_no_id = fields.Char(string='Check No.')

    currency_id = fields.Many2one(
        'res.currency', related="payment_id.currency_id", ondelete='cascade')
    total_amount = fields.Monetary(
        "Total Amount", 'currency_id', compute='_get_total_amount')
    amount_in_words = fields.Char(string="Amount in Words")
    description = fields.Text(string="Description")

    # ===============================================================
    """States and related fields and methods"""
    # ===============================================================
    state = fields.Selection(STATUS, string="Status",
                             default="draft", readonly=True, copy=False)

    drafted_by_id = fields.Many2one(
        'res.users', string="Drafted By: ", ondelete='cascade',
        readonly=True
    )

    date_submitted = fields.Datetime(
        string='Date Submitted',
        readonly=True

    )
    submitted_by_id = fields.Many2one(
        'res.users', string="Submitted By: ", ondelete='cascade',
        readonly=True
    )

    date_confirmed = fields.Datetime(
        string='Date Confirmed',
        readonly=True

    )
    confirmed_by_id = fields.Many2one(
        'res.users', string="Confirmed By: ", ondelete='cascade',
        readonly=True
    )

    date_verified = fields.Datetime(
        string='Date Verified',
        readonly=True
    )

    verified_by_id = fields.Many2one(
        'res.users', string="Verified By: ", ondelete='cascade',
        readonly=True
    )

    date_approved = fields.Datetime(
        string='Date Approved',
        readonly=True
    )
    approved_by_id = fields.Many2one(
        'res.users', string="Approved By: ", ondelete='cascade',
        readonly=True
    )

    date_canceled = fields.Datetime(
        string='Date Verified',
        readonly=True
    )
    canceled_by_id = fields.Many2one(
        'res.users', string="Canceled By: ", ondelete='cascade',
        readonly=True
    )

    # ===============================================================
    """One2many Fields"""
    # ===============================================================
    invoice_ids = fields.One2many(
        'check.voucher.particulars', 'check_voucher_id')
    account_ids = fields.One2many(
        'check.voucher.account_distribution', 'check_voucher_id')
    account_payment_id = fields.One2many(
        'account.payment', 'check_voucher_id', string='Account Payment ID', ondelete='cascade')
    # ===============================================================

    @api.constrains('total_amount')
    def tally_total_amount(self):
        for rec in self:
            if rec.total_amount != rec.payment_id.amount:
                raise ValidationError(
                    _('Total Amount must be exactly the same as Payment Amount'))

    @api.multi
    def submit_voucher(self):
        debit_total = 0
        credit_total = 0
        for i in self:
            for j in i.account_ids:
                debit_total += round(j.debit_amount,2)
                credit_total += round(j.credit_amount,2)
                _logger.info(
                    "\n\n\nDebit Amount: \n%s\n Credit Amount: \n\n\n\n" % (str(debit_total)))
        if debit_total != credit_total:
            raise ValidationError(
                _("Total Debit Amount must be the same as Total Credit Amount"))
        elif debit_total != i.payment_id.amount and credit_total != i.payment_id.amount:
            raise ValidationError(
                _("Total Debit Amount and Credit Amount must be the same as Payment Amount"))
        elif self.total_amount != self.payment_id.amount:
            raise ValidationError(
                _('Total Amount must be exactly the same as Payment Amount'))
        else:
            self.write({
                'state': 'submitted',
                'date_submitted': datetime.now(),
                'submitted_by_id': self._uid,
            })
        return True

    @api.multi
    def confirm_voucher(self):
        self.write({
            'state': 'confirmed',
            'date_confirmed': datetime.now(),
            'confirmed_by_id': self._uid,
        })
        return True

    @api.multi
    def verify_voucher(self):
        self.write({
            'state': 'verified',
            'date_verified': datetime.now(),
            'verified_by_id': self._uid,
        })
        return True

    @api.multi
    def approve_voucher(self):
        self.write({
            'state': 'approved',
            'date_approved': datetime.now(),
            'approved_by_id': self._uid,
        })
        return True

    @api.multi
    def cancel_voucher(self):
        self.write({
            'state': 'canceled',
            'date_canceled': datetime.now(),
            'canceled_by_id': self._uid,
        })

    @api.onchange('invoice_ids', 'invoice_ids.amount')
    def _get_total_amount(self):
        for i in self:
            total = 0
            for rec in i.invoice_ids:
                total += rec.amount
            i.total_amount = total

    @api.onchange('total_amount', 'currency_id')
    def _onchange_amount(self):
        if self.currency_id:
            self.amount_in_words = self.currency_id.amount_to_text(
                self.total_amount)

    # Overriding the create method to add sequencing to Iteration ID
    @api.model
    def create(self, vals):
        if vals.get('voucher_id_seq', _('New')) == ('New'):
            vals['voucher_id_seq'] = self.env['ir.sequence'].next_by_code(
                'voucher.number.sequence') or _('New')
            vals['drafted_by_id'] = self._uid
        result = super(CheckVoucher, self).create(vals)
        self.env['account.payment'].browse(vals.get('payment_id')).write({
            'check_voucher_id': result.id})
        return result

    @api.multi
    def _compute_total_debit(self):
        total_debit = sum([i.debit_amount for i in self.account_ids])
        _logger.info(f'Total Debit:\n\n\n{str(total_debit)}\n\n\n')
        return total_debit

    @api.multi
    def _compute_total_credit(self):
        total_credit = sum([i.credit_amount for i in self.account_ids])
        return total_credit

    @api.multi
    def _compute_total_invoice(self):
        total_invoice = sum(i.amount for i in self.invoice_ids)
        return total_invoice


class Particulars(models.Model):
    _name = "check.voucher.particulars"
    # _inherit = 'account.payment'

    partner_id = fields.Many2one(
        'res.partner', string='Partner', ondelete='cascade')
    check_voucher_id = fields.Many2one(
        'check.voucher', string='Payee: ', ondelete='cascade')
    invoice_id = fields.Many2one('account.invoice',
                                 string="Invoice No.",
                                 ondelete='cascade',
                                 )
    account_payment = fields.Many2one('account.payment',
                                      string='Payment ID',
                                      ondelete='cascade'
                                      )
    description = fields.Text(string="Description", required=True)

    currency_id = fields.Many2one(
        'res.currency', related='check_voucher_id.payment_id.currency_id')
    amount = fields.Monetary("Amount",
                             'currency_id',
                             )

    @api.onchange('invoice_id', 'amount')
    def _on_change_amount(self):
        self.amount = self.invoice_id.residual if self.invoice_id.residual else self.amount


class AccountDistribution(models.Model):
    _name = "check.voucher.account_distribution"

    check_voucher_id = fields.Many2one('check.voucher', string='Payee: ')
    account_title = fields.Many2one('account.account', string='Account Title')
    debit_amount = fields.Float(string='Debit')
    credit_amount = fields.Float(string='Credit')


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    _rec_name = 'name'

    check_voucher_id = fields.Many2one(
        'check.voucher', string='Voucher', ondelete='cascade')

    particulars_ids = fields.One2many(
        'check.voucher.particulars',
        'account_payment',
        string="Particulars ID",
        ondelete='cascade')

    journal_type = fields.Selection(
        string='Journal Type', related='journal_id.type')

    voucher_state = fields.Selection(
        string='Voucher State', related='check_voucher_id.state'
    )

    @api.multi
    def name_get(self):
        res = super(AccountPayment, self).name_get()
        data = []
        a = self.env['account.payment'].search([('state', 'in', [('draft')])])
        for i in a:
            display_value = '%s [%s]' % (i.journal_id.code, i.payment_date)
            data.append((i.id, display_value))
        b = self.env['account.payment'].search(
            [('state', 'not in', [('draft')])])
        for i in b:
            data.append((i.id, i.name))

        if data:
            return data
        else:
            return res
