# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class OvertimeCompanyrRule(models.Model):
    _name = 'overtime.company.rule'

    overtime_type_id = fields.Many2one('hr.overtime.type', string="Overtime Type", ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True)
    name = fields.Char(string="Name", required=True, help="Responsible of computing the equivalent of Overtime during Payslip Generation.")
    salary_rule_id = fields.Many2one('hr.salary.rule', string="Salary Rule Associated", required=True,
                                     domain="[('company_id', 'in', [False, company_id])]",
                                     help="Responsible of computing the equivalent of Overtime during Payslip Generation.")



class HROvertimeType(models.Model):
    _name = 'hr.overtime.type'
    _rec_name = 'code'

    formula = fields.Html(string="Formula")
    company_rule_ids = fields.One2many('overtime.company.rule', 'overtime_type_id', string="Company Salary Rules")
    code = fields.Selection([('OT','Ordinary Overtime (125%)'),
                             ('OTND','Ordinary Overtime + Night Differential'),
                             ('RD','Restday'),
                             ('RHD','Regular Holiday (200%)'),
                             ('SHD','Special Holiday (130%)'),
                             ('DHD','Double Holiday'),
                             ('RHDOT','Regular Holiday Overtime (260%)'),
                             ('SHDOT','Special Holiday Overtime (169%)'),
                             ('DHDOT','Double Holiday + Overtime'),
                             ('RHDND','Regular Holiday + Night Differential'),
                             ('SHDND','Special Holiday + Night Differential'),
                             ('DHDND','Double Holiday + Night Differential'),
                             ('RHDOTND','Regular Holiday + Night Differential + Overtime'),
                             ('SHDOTND','Special Holiday + Night Differential + Overtime'),
                             ('DHDOTND','Double Holiday + Night Differential + Overtime'),
                             ('RDOT','Restday + Overtime'),
                             ('RDND','Restday + Night Differential'),
                             ('RDOTND','Restday + Night Differential + Overtime'),
                             ('RHDRD','Regular Holiday + Restday'),
                             ('SHDRD','Special Holiday + Restday'),
                             ('DHDRD','Double Holiday + Restday'),
                             ('RHDRDOT','Regular Holiday + Restday + Overtime'),
                             ('SHDRDOT','Special Holiday + Restday + Overtime'),
                             ('DHDRDOT','Double Holiday + Restday + Overtime'),
                             ('RHDRDND','Regular Holiday + Restday + Night Differential'),
                             ('SHDRDND','Special Holiday + Restday + Night Differential'),
                             ('DHDRDND','Double Holiday + Restday + Night Differential'),
                             ('RHDRDOTND','Regular Holiday + Restday + Night Differential + Overtime'),
                             ('SHDRDOTND','Special Holiday + Restday + Night Differential + Overtime'),
                             ('DHDRDOTND','Double Holiday + Restday + Night Differential + Overtime'),
                             ],string="Select Code", required=True, help="Select Code that is equal to the Type name")

    @api.constrains('company_rule_ids', 'formula')
    def _check_data(self):
        for i in self:
            duplicate_code = self.search([('code', '=', self.code), ('id', 'not in', [self.id])])
            if duplicate_code[:1]: raise ValidationError(_('%s already exist'%(self.code)))
            duplicate_company = [rec.company_id.id for rec in i.company_rule_ids]
            if len(duplicate_company) != len(set(duplicate_company)): raise ValidationError(_('Duplication of Company/Branch is not allowed.'))
