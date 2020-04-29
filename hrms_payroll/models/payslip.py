'''
Created on 04 of December 2019

@author: Dennis
'''

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
import calendar
from dateutil.relativedelta import relativedelta
from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp


class HRSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    taxable_rule = fields.Selection([('increase', 'Increase'), ('decrease', 'Decrease')], string="Taxable Rule")
    net_salary = fields.Boolean(string="Use for Net Salary")
    #
    @api.multi
    def _compute_rule(self, localdict):
        """
        :param localdict: dictionary containing the environement in which to compute the rule
        :return: returns a tuple build as the base/amount computed, the quantity and the rate
        :rtype: (float, float, float)
        """
        self.ensure_one()
        if self.amount_select == 'fix':
            try:
                return self.amount_fix, float(safe_eval(self.quantity, localdict)), 100.0
            except:
                raise UserError(_('Wrong quantity defined for salary rule %s (%s).') % (self.name, self.code))
        elif self.amount_select == 'percentage':
            try:
                return (float(safe_eval(self.amount_percentage_base, localdict)),
                        float(safe_eval(self.quantity, localdict)),
                        self.amount_percentage)
            except:
                raise UserError(_('Wrong percentage base or quantity defined for salary rule %s (%s).') % (self.name, self.code))
        else:
            # try:
            safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
            return float(localdict['result']), 'result_qty' in localdict and localdict['result_qty'] or 1.0, 'result_rate' in localdict and localdict['result_rate'] or 100.0
            # except:
            #     raise UserError(_('Wrong python code defined for salary rule %s (%s).') % (self.name, self.code))


class HRPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    cutoff_template_id = fields.Many2one('payroll.cutoff.template', string="Attendance Cutoff Group", required=True)
    cutoff_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('bi-monthly', 'Bi-monthly'),
        ('weekly', 'Weekly'),
        ], string="Attendance Cutoff Type", default='monthly', related="cutoff_template_id.cutoff_type", store=True)
    cutoff = fields.Selection([('1', '1st Cutoff'), ('2', '2nd Cutoff'), ('3', '3rd Cutoff'), ('4', 'Forth Cutoff')], string="Cutoff")
    month_year = fields.Char(string="Cutoff Month", help="MM/YYYY", required=True)
    compute_thirtheenth_month = fields.Boolean(string="Compute 13th Month")

    @api.constrains('cutoff', 'cutoff_template_id')
    def check_cutoff(self):
        if self.cutoff in ['3', '4'] and self.cutoff_template_id.cutoff_type == 'bi-monthly':
            raise ValidationError(_('Invalid input!\nBi-monthly has only 1st and 2nd cutoff.'))

    @api.multi
    def get_dates(self, month_end_cutoff):
        month_date = datetime.strptime(self.month_year, "%m/%Y")
        try:
            prev_last_month_date = calendar.monthrange(month_date.year,month_date.month - 1)
            if prev_last_month_date[1] < month_end_cutoff:
                date_start = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month - 1, prev_last_month_date[1]), DF) + timedelta(days=1)
            else:
                date_start = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month - 1, month_end_cutoff), DF) + timedelta(days=1)
        except:
            prev_last_month_date = calendar.monthrange(month_date.year - 1, 12)
            if prev_last_month_date[1] < month_end_cutoff:
                date_start = datetime.strptime("%s-%s-%s"%(month_date.year-1, 12, prev_last_month_date[1]), DF) + timedelta(days=1)
            else:
                date_start = datetime.strptime("%s-%s-%s"%(month_date.year-1, 12, month_end_cutoff), DF) + timedelta(days=1)

        last_month_date = calendar.monthrange(month_date.year,month_date.month)
        if last_month_date[1] < month_end_cutoff:
            date_end = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month, last_month_date[1]), DF)
        else:
            date_end = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month, month_end_cutoff), DF)
        return [date_start, date_end]


    @api.onchange("cutoff_template_id", "month_year", "cutoff")
    def _onchange_month_year(self):
        if self.month_year and self.cutoff_template_id:
            self._check_month_year_format()
            self.check_cutoff()
            month_date = datetime.strptime(self.month_year, "%m/%Y")
            if self.cutoff_template_id.cutoff_type in ['monthly']:
                date_start, date_end = self.get_dates(self.cutoff_template_id.monthly_date)
            elif self.cutoff_template_id.cutoff_type == 'bi-monthly' and self.cutoff:
                date_start, date_end = self.get_dates(self.cutoff_template_id.bimonthly_date)
                if self.cutoff == '1':
                    date_end = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month, self.cutoff_template_id.bimonthly_first_date), DF)
                elif self.cutoff == '2':
                    date_start = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month, self.cutoff_template_id.bimonthly_first_date), DF) + timedelta(days=1)
            elif  self.cutoff_template_id.cutoff_type in ['weekly']:
                today = date.today()
                while today.weekday() != int(self.cutoff_template_id.day_of_week):
                    today -= timedelta(days=1)
                date_end = today
                date_start = today - timedelta(days=6)
            try:
                self.date_start = date_start.strftime(DF)
                self.date_end = date_end.strftime(DF)
            except: pass

    @api.constrains("month_year")
    def _check_month_year_format(self):
        try:
            date = datetime.strptime(self.month_year, "%m/%Y")
        except:
            raise ValidationError(_("Cutoff Month format must be in 'MM/YYYY'"))

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    # @api.depends('date_to', 'date_from')
    # def _get_paylip_recording_period(self):
    #     for i in self:
    #         i.payslip_period = i.date_to.strftime("%m/%Y")

    for_final_payment = fields.Boolean(string="For Final Payment", track_visibility=True)
    payslip_period = fields.Char(string="Cutoff Month", help="MM/YYYY", required=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)#, store=True, compute="_get_paylip_recording_period")
    compute_thirtheenth_month = fields.Boolean(string="Commpute 13th Month", readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    paid_thirtheenth_month = fields.Boolean(string="Compute 13th Month", readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)

    cutoff_template_id = fields.Many2one('payroll.cutoff.template', string="Attendance Cutoff Group", related="contract_id.cutoff_template_id", store=True)
    cutoff_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('bi-monthly', 'Bi-monthly'),
        ('weekly', 'Weekly'),
        ], string="Attendance Cutoff Type", default='monthly', related="cutoff_template_id.cutoff_type", store=True, track_visibility=True)
    cutoff = fields.Selection([('1', '1st Cutoff'), ('2', '2nd Cutoff'), ('3', '3rd Cutoff'), ('4', 'Forth Cutoff')], string="Cutoff",
                              readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)


    @api.multi
    def get_dates(self, month_end_cutoff):
        month_date = datetime.strptime(self.payslip_period, "%m/%Y")
        try:
            prev_last_month_date = calendar.monthrange(month_date.year,month_date.month - 1)
            if prev_last_month_date[1] < month_end_cutoff:
                date_start = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month - 1, prev_last_month_date[1]), DF) + timedelta(days=1)
            else:
                date_start = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month - 1, month_end_cutoff), DF) + timedelta(days=1)
        except:
            prev_last_month_date = calendar.monthrange(month_date.year - 1, 12)
            if prev_last_month_date[1] < month_end_cutoff:
                date_start = datetime.strptime("%s-%s-%s"%(month_date.year-1, 12, prev_last_month_date[1]), DF) + timedelta(days=1)
            else:
                date_start = datetime.strptime("%s-%s-%s"%(month_date.year-1, 12, month_end_cutoff), DF) + timedelta(days=1)

        last_month_date = calendar.monthrange(month_date.year,month_date.month)
        if last_month_date[1] < month_end_cutoff:
            date_end = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month, last_month_date[1]), DF)
        else:
            date_end = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month, month_end_cutoff), DF)
        return [date_start, date_end]


    @api.onchange("cutoff_template_id", "payslip_period", "cutoff")
    def _onchange_month_year(self):
        if self.payslip_period and self.cutoff_template_id:
            self._check_month_year_format()
            self.check_cutoff()
            month_date = datetime.strptime(self.payslip_period, "%m/%Y")
            if self.cutoff_template_id.cutoff_type in ['monthly']:
                date_start, date_end = self.get_dates(self.cutoff_template_id.monthly_date)
            elif self.cutoff_template_id.cutoff_type == 'bi-monthly' and self.cutoff:
                date_start, date_end = self.get_dates(self.cutoff_template_id.bimonthly_date)
                if self.cutoff == '1':
                    date_end = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month, self.cutoff_template_id.bimonthly_first_date), DF)
                elif self.cutoff == '2':
                    date_start = datetime.strptime("%s-%s-%s"%(month_date.year,month_date.month, self.cutoff_template_id.bimonthly_first_date), DF) + timedelta(days=1)
            elif  self.cutoff_template_id.cutoff_type in ['weekly']:
                today = date.today()
                while today.weekday() != int(self.cutoff_template_id.day_of_week):
                    today -= timedelta(days=1)
                date_end = today
                date_start = today - timedelta(days=6)
            try:
                self.date_from = date_start.strftime(DF)
                self.date_to = date_end.strftime(DF)
            except: pass


    @api.constrains("payslip_period")
    def _check_month_year_format(self):
        try:
            date = datetime.strptime(self.payslip_period, "%m/%Y")
        except:
            raise ValidationError(_("Cutoff Month format must be in 'MM/YYYY'"))

    @api.multi
    def mark_13th_payout(self):
        if self.compute_thirtheenth_month:
            nov_from = datetime.strptime("%s-11-01"%(self.date_from.year - 1), DF)
            nov_to = datetime.strptime("%s-11-30"%(self.date_from.year), DF)
            employee = self.env['hr.employee'].browse(self.employee_id)
            payslip_record = self.env['hr.payslip'].search([
                                                ('employee_id', '=', self.employee_id.id),
                                                ('state', '=', 'done'),
                                                ('date_to', '>=', nov_from),
                                                ('date_to', '<=', nov_to)
                                            ])
            for i in payslip_record:
                i.write({'paid_thirtheenth_month': True})

    @api.multi
    def action_payslip_done(self):
        res = super(HRPayslip, self).action_payslip_done()
        self.mark_13th_payout()
        return res

    @api.constrains('cutoff', 'cutoff_template_id')
    def check_cutoff(self):
        if self.cutoff in ['3', '4'] and self.cutoff_template_id.cutoff_type == 'bi-monthly':
            raise ValidationError(_('Invalid input!\nBi-monthly has only 1st and 2nd cutoff.'))




class HRPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    payslip_period = fields.Char(string="Recording Period", store=True, related="slip_id.payslip_period")
    date_from = fields.Date(string="Date From", store=True, related="slip_id.date_from")
    date_to = fields.Date(string="Date To", store=True, related="slip_id.date_to")
    employee_id = fields.Many2one("hr.employee", string="Employee", related="slip_id.employee_id")

    @api.constrains('cutoff', 'cutoff_template_id')
    def check_cutoff(self):
        if self.cutoff in ['3', '4'] and self.cutoff_template_id.cutoff_template_id.cutoff_type == 'bi-monthly':
            raise ValidationError(_('Invalid input!\nBi-monthly has only 1st and 2nd cutoff.'))
