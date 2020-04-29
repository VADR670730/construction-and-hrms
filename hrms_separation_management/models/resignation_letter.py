from odoo import models, fields, api, _
from datetime import date, timedelta
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HRMSResignationLetter(models.Model):
    _name = "hr.resignation.letter"
    _description = "Resignation Letter"
    _inherit = ["mail.thread", "mail.activity.mixin", "resource.mixin"]


    name = fields.Many2one('hr.employee', "Employee Name", required=True)
    resignation_date = fields.Date("Resignation Date Request", required=True)
    effective_date = fields.Date("Effective Date")
    relieved_date = fields.Date("Relieved Date")
    reason = fields.Many2one('hr.resignation.reason', "Reason", required=True)
    # reason = fields.Selection([
    #     ('underappreciated', 'Underappreciated (resignation)'),
    #     ('lack_of_proper_compensation',
    #      'Lack of Proper Compensation (resignation)'),
    #     ('unrealistic_goals', 'Unrealistic Goals (resignation)'),
    #     ('lack_of_joy', 'Lack of a Joyful Environment (resignation)'),
    #     ('lack_of_work', 'lack of work/life balance (resignation)'),
    #     ('upward_mobility', 'No upward mobility (resignation)'),
    #     ('prioritize_health', 'Prioritize  health (retirement)'),
    #     ('caring_for_family', 'Caring for Family (retirement)'),
    #     ('violation', 'Violating Company Policy  (termination)'),
    #     ('poor_performance', 'Poor Performance (termination)'),
    #     ('misconduct', 'Misconduct (termination)'),
    #     ('insubordination', 'Insubordination (termination)')
    # ], string="Reason", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('confirm', 'Confirm'),
        ('approve', 'Approved'),
    ], string="Status", default="draft", readonly=True, copy=False)
    letter = fields.Html(string='Resignation Letter')
    separation_parent_id = fields.Many2one('hr.separation',
                                           'Separation Parent ID',
                                           ondelete="cascade")

    date_submitted = fields.Date("Date Submitted")
    submitted_by = fields.Many2one('res.users', 'Submitted By')
    date_confirm = fields.Date("Date Confirmed")
    confirm_by = fields.Many2one('res.users', 'Confirmed By')
    date_approved = fields.Date("Date Approved")
    approved_by = fields.Many2one('res.users', 'Approved By')


    @api.multi
    def submit(self):
        for rec in self:
            duplicate = self.search([('name', '=', rec.name.id),
                                     ('id', '!=', rec.id),
                                     ('state', '=', 'submit')])
            if duplicate:
                raise UserError('''Duplicate Resignation Letter.
                                Please Check the other records for Reference''')
            else:
                rec.date_submitted = date.today()
                user_id = self.env['res.users'].browse(self._context.get('uid'))
                rec.submitted_by = user_id.id
                return self.write({'state': 'submit'})

    @api.multi
    def confirm(self):
        self.date_confirm = date.today()
        user_id = self.env['res.users'].browse(self._context.get('uid'))
        self.confirm_by = user_id.id
        return self.write({'state': 'confirm',
                           'effective_date': date.today()})

    @api.multi
    def approved(self):
        self.date_approved = date.today()
        user_id = self.env['res.users'].browse(self._context.get('uid'))
        self.approved_by = user_id.id
        relieved = self.effective_date + timedelta(days=30)
        return self.write({'state': 'approve',
                           'relieved_date':relieved})

    @api.onchange('name')
    def _duplicate_employee_entry(self):
        if self.name:
            duplicate = self.search([('name', '=', self.name.id),
                                     ('id', '!=', self._origin.id),
                                     ('state', '=', 'submit')])
            if duplicate:
                return {
                    'warning': {
                        'title': "Duplicate Entry",
                        'message': """Duplicate Resignation Letter.
                        Please Check the other records for Reference"""
                    }
                }

    @api.constrains('name')
    def check_duplicate_true(self):
        if self.name:
            duplicate = self.search([('name', '=', self.name.id),
                                     ('id', '!=', self.id),
                                     ('state', '=', 'submit')])
            if duplicate:
                raise UserError('''Duplicate Resignation Letter.
                                Please Check the other records for Reference''')


class HRMSResignationReason(models.Model):
    _name = "hr.resignation.reason"
    _description = "Resignation Reason"
    _inherit = ["mail.thread", "mail.activity.mixin", "resource.mixin"]

    name = fields.Char("Resignation Reason")
