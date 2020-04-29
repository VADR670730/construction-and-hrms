# coding: utf-8
from odoo import models, fields, api
from datetime import date
from logging import getLogger


def log(*to_output):
    getLogger().info("\n\n\n{0}\n\n".format(to_output))


class EmployeeWorkHistory(models.Model):
    _inherit = 'hr.employee'

    work_history_ids = fields.One2many('hr.candidate.work.history',
                                       'employee_id',
                                       string="Work History")


class WorkHistory(models.Model):
    _name = 'hr.work.history'

    employee_id = fields.Many2one('hr.employee', ondelete="cascade")
    job_id = fields.Many2one('hr.job', "Position")
    company_name = fields.Char("Company Name", required=True)
    address = fields.Char("Address", required=True)
    line_of_business = fields.Char("Line of Business")
    date_started = fields.Date()
    date_exited = fields.Date()
    years_of_service = fields.Char('Year(s) of Service',
                                   compute="_get_years_of_service")

    statutory_requirements = fields.Float(string="SSS, GSIS, PHIC, HDMF & union Dues", store=True)
    nontax_other_benefits = fields.Float(string="Other Benefits & 13th Mo. Pay", store=True)
    deminimis = fields.Float(string="Nontaxable DeMinimis Benefits", store=True)
    holiday = fields.Float(string="Holiday Pay", store=True)
    overtime = fields.Float(string="Overtime Pay", store=True)
    night_diff = fields.Float(string="Night Shift Differential", store=True)
    hazard = fields.Float(string="Hazard Pay", store=True)
    nontax_salaries_other_comp = fields.Float(string="Salaries & Others Comp", store=True)
    total_nontax = fields.Float("Total", store=True, compute="_get_total_nontaxable")

    night_diff = fields.Float(string="Taxable Basic Salary", store=True)
    tax_other_benefits = fields.Float(string="Other Benefits & 13th Mo. Pay", store=True)
    tax_salaries_other_comp = fields.Float(string="Salaries & Others Comp", store=True)
    total_tax = fields.Float("Total", store=True, compute="_get_total_taxable")

    premium_paid = fields.Float(string="Premium Paid on Health & other Hops. Insurance", store=True)
    exempt_amount = fields.Float(string="Exemption Amount", store=True)
    tax_withheld = fields.Float(string="Tax Withheld", store=True)

    gross = fields.Float(string="Gross Compensation Income", store=True)
    net_tax = fields.Float(string="Net Taxable Income", store=True)
    tax_due = fields.Float(string="Tax Due", store=True)
    amount_withheld = fields.Float(string="Amount Withheld and paid for in December", store=True)
    over_withheld = fields.Float(string="Over Withheld Tax refunded to Employees", store=True)
    tax_withheld_adjusted = fields.Float(string="Amt. of Tax Withheld as Adjusted", store=True)
    substitute_filing = fields.Selection([
        ('yes', 'YES'),
        ('no', 'No')
    ], string="Substitute filing")

    @api.depends('statutory_requirements','nontax_other_benefits',
                 'deminimis','holiday','overtime','night_diff','hazard',
                 'nontax_salaries_other_comp')
    def _get_total_nontaxable(self):
        for rec in self:
            rec.total_nontax = (rec.statutory_requirements
                                + rec.nontax_other_benefits
                                + rec.deminimis
                                + rec.holiday
                                + rec.overtime
                                + rec.night_diff
                                + rec.hazard
                                + rec.nontax_salaries_other_comp
                                + rec.total_nontax)

    @api.depends('night_diff','tax_other_benefits',
                 'tax_salaries_other_comp')
    def _get_total_taxable(self):
        for rec in self:
            rec.total_tax =(rec.night_diff
                            + rec.tax_other_benefits
                            + rec.tax_salaries_other_comp)

    @api.depends('date_started','date_exited')
    def _get_years_of_service(self):
        for rec in self:
            if rec.date_started:
                years_services = str(int((date.today()
                                          - rec.date_started).days
                                         / 365)) + " Year(s)"
                month = int((date.today()
                             - rec.date_started).days * 0.0328767)
                if month > 12:
                    month_services = str(month % 12) + " Month(s)"
                else:
                    month_services = str(month) + " Month(s)"
                rec.years_of_service = years_services + " , " + month_services
