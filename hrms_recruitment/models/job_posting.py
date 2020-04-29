# -*- coding: utf-8 -*-
from odoo import models, fields, api


class JobPosting(models.Model):
    _inherit = 'hr.job'

    personnel_requisition_id = fields.Many2one('hr.personnel.requisition')
    proposed_salary = fields.Float(
        string="Proposed Salary",
        related='personnel_requisition_id.proposed_salary',
        readonly=True,
        store=True
    )

    skills_ids = fields.Many2many(
        'hr.employee.skills',
        string="Skills")

    job_qualification = fields.Text(string="Qualification")

    no_of_recruitment = fields.Integer(string='Expected New Employees', copy=False,
        help='Number of new employees you expect to recruit.', default=1, compute='get_expected_new_employees')

    @api.depends('personnel_requisition_id')
    def get_expected_new_employees(self):
        for rec in self:
            requisition_records_count = self.env['hr.personnel.requisition'].search([('job_position_id','=',rec.id),('state','in',['approved'])])
            requisition_record_no_of_emps = sum(rec.expected_new_employee for rec in requisition_records_count)
            rec.no_of_recruitment = requisition_record_no_of_emps