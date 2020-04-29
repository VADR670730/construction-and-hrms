'''
Created on 06 of September 2019

@author: Dennis
'''

from odoo import api, fields, models, tools, SUPERUSER_ID, _

class HRPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    company_id = fields.Many2one('res.company', string="Company/Branch", required=True,
                                  default=lambda self: self.env['res.company']._company_default_get('hr.payslip.run'))


class HrSalaryRuleCategory(models.Model):
    _inherit = 'hr.salary.rule.category'

    sequence = fields.Integer(string="Sequence", default=5)
    
