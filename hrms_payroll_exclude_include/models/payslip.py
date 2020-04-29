'''
Created on 07 of December 2019
@author: Dennis
'''

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

import logging
_logger = logging.getLogger("_name_")


class HRSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    can_exclude = fields.Boolean(string="Can be Included/Excluded", help="This specific rule can be included on a certain cutoff only")


class HRContract(models.Model):
    _inherit = 'hr.contract'

    salary_rule_template_id = fields.Many2one('hr.salary.rule.template', string="Cutoff Salary Rules (Include/Exclude Template)", domain="[('cutoff_template_id', '=', cutoff_template_id), ('salary_structure_id', '=', struct_id)]")


    @api.multi
    def _check_computation(self, contract, payslip, code):
        contract = self.browse(contract.id)
        if not contract.cutoff_template_id.cutoff_type in ['monthly'] or not contract.salary_rule_template_id:
            return True
        elif contract.salary_rule_template_id:
            rule = self.env['hr.salary.rule.template.line'].search([('template_id', '=', contract.salary_rule_template_id .id), ('rule_id.code', '=', code)], limit=1)
            if rule[:1]:
                if rule.include_on == payslip.cutoff:
                    return True
                else: return False
        else: return True


class HRSalaryRuleTemplateLine(models.Model):
    _name = 'hr.salary.rule.template.line'

    @api.model
    def _get_cutoff_type(self):
        vals=[('1', '1st Cutoff'), ('2', '2nd Cutoff'), ('3', '3rd Cutoff'), ('4', 'Forth Cutoff')]
        return vals

    template_id = fields.Many2one('hr.salary.rule.template', string="Template")
    rule_id = fields.Many2one('hr.salary.rule', string="Salary Rule", required="True")
    include_on = fields.Selection(string="Include Only On", selection=_get_cutoff_type, default='1', required=True)
    computation_code = fields.Text(string="Computation Code", related="rule_id.amount_python_compute")

    @api.constrains('include_on', 'template_id')
    def check_cutoff(self):
        if self.include_on in ['3', '4'] and self.template_id.cutoff_template_id.cutoff_type == 'bi-monthly':
            raise ValidationError(_('Invalid input!\nBi-monthly has only 1st and 2nd cutoff.'))

    @api.onchange('template_id')
    def onchange_template(self):
        if self.template_id and self.template_id.salary_structure_id:
            rules = []
            for i in self.template_id.salary_structure_id.rule_ids:
                if i.can_exclude:
                    rules.append(i.id)
            return {
                    'domain': {
                        'rule_id': [('id', 'in', self.template_id.salary_structure_id.ids)]
                        }
                    }


class HRSalaryRuleTemplate(models.Model):
    _name = 'hr.salary.rule.template'

    name = fields.Char(string="Name", required=True)
    cutoff_template_id = fields.Many2one('payroll.cutoff.template', string="Attendance Cutoff Type", required=True, domain="[('cutoff_type', 'not in', ['monthly'])]")
    salary_structure_id = fields.Many2one('hr.payroll.structure', string="Salary Structure", required=True)
    line_ids = fields.One2many('hr.salary.rule.template.line', 'template_id',string="Rules")
