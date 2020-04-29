# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class Assessment(models.Model):
    _name = "hr.assessment"
    _rec_name = "applicant_name"

    name = fields.Char(string="Test Name",
                       required=True
                       )
    applicant_id = fields.Many2one('hr.applicant', string="Applicant")
    applicant_name = fields.Char(string="Applicant")
    job_id = fields.Many2one('hr.job', string="Job Position")
    test_type = fields.Selection(
        string='Test Type',
        selection=[
            ('cognitive', 'Cognitive'),
            ('aptitude', 'Aptitude'),
            ('personality', 'Personality'),
            ('skill', 'Skill'),
            ('physical', 'Physical'),
        ]
    )
    website = fields.Char(string="Source Website")
    assessment_date = fields.Date(string="Date of Assessment")

    number_of_items = fields.Integer(
        string='Number of Items',
    )
    correct_items = fields.Integer(string="Correct Items")

    result = fields.Selection(
        string='Result',
        selection=[
            ('passed', 'Passed'),
            ('failed', 'Failed')]
    )
    checked_by_id = fields.Many2one('hr.employee')
