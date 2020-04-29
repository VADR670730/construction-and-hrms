# coding: utf-8
from odoo import models, fields, api
from logging import getLogger


def log(**to_output):
    getLogger().info("\n\n\n{0}\n\n".format(to_output))


class InheritEmployeeAppraisal(models.Model):
    _inherit = 'hr.employee'

    manager_appraisal = fields.Boolean(string='Appraisal by Manager',
                                       compute="_get_values_from_appraisal",
                                       help="This employee will be appraised by his managers")
    manager_ids = fields.Many2many('hr.employee', 'appraisal_manager_rel',
                                   'hr_appraisal_id',
                                   compute='_get_values_from_appraisal')
    manager_survey_id = fields.Many2one('survey.survey',
                                        string="Manager's Appraisal",
                                        compute="_get_values_from_appraisal")
    employee_appraisal = fields.Boolean(compute="_get_values_from_appraisal",
                                        help="This employee will do a self-appraisal")
    employee_survey_id = fields.Many2one('survey.survey',
                                         compute="_get_values_from_appraisal",
                                         string='Self Appraisal')
    collaborators_appraisal = fields.Boolean(string='Collaborator',
                                             compute='_get_values_from_appraisal',
                                             help="This employee will be appraised by his collaborators")
    collaborators_ids = fields.Many2many('hr.employee',
                                         'appraisal_subordinates_rel',
                                         'hr_appraisal_id',
                                         compute='_get_values_from_appraisal')
    collaborators_survey_id = fields.Many2one('survey.survey',
                                              string="Collaborator's Appraisal",
                                              compute='_get_values_from_appraisal')
    colleagues_appraisal = fields.Boolean(string='Colleagues Appraisal',
                                          compute='_get_values_from_appraisal',
                                          help="This employee will be appraised by his colleagues")
    colleagues_ids = fields.Many2many('hr.employee',
                                      'appraisal_colleagues_rel',
                                      'hr_appraisal_id',
                                      compute='_get_values_from_appraisal',
                                      string="Colleagues")
    colleagues_survey_id = fields.Many2one('survey.survey',
                                           compute='_get_values_from_appraisal',
                                           string="Colleague's Appraisal")

    date_close = fields.Date(string='Appraisal Deadline',
                             compute='_get_values_from_appraisal')
    date_final_interview = fields.Date(string="Final Interview",
                                       index=True,
                                       track_visibility='onchange',
                                       compute='_get_values_from_appraisal')

    @api.depends('name')
    def _get_values_from_appraisal(self):
        for rec in self:
            appraisal = self.env['hr.appraisal'].search([
                ('employee_id', '=', rec.id)
            ])

            rec.manager_appraisal = appraisal.manager_appraisal
            rec.manager_ids = appraisal.manager_ids
            rec.manager_survey_id = appraisal.manager_survey_id
            rec.employee_appraisal = appraisal.employee_appraisal
            rec.employee_survey_id = appraisal.employee_survey_id
            rec.collaborators_appraisal = appraisal.collaborators_appraisal
            rec.collaborators_ids = appraisal.collaborators_ids
            rec.collaborators_survey_id = appraisal.collaborators_survey_id
            rec.colleagues_appraisal = appraisal.colleagues_appraisal
            rec.colleagues_ids = appraisal.colleagues_ids
            rec.colleagues_survey_id = appraisal.colleagues_survey_id
            rec.date_close = appraisal.date_close
            rec.date_final_interview = appraisal.date_final_interview
