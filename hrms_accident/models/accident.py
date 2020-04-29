# coding: utf-8
from odoo import models, fields, api, _
from datetime import date
from logging import getLogger


def log(**to_output):
    getLogger().info("\n\n\n{0}\n\n".format(to_output))


class InheritEmployeeAccident(models.Model):
    _inherit = 'hr.employee'

    accident_ids = fields.One2many('hrms.accident', 'employee_id',
                                   compute="_get_accidents")

    @api.depends('name')
    def _get_accidents(self):
        for rec in self:
            rec.accident_ids = self.env['hrms.accident'].search([
                ('employee_id', '=', rec.id)
            ])


class WorkAccident(models.Model):
    _name = 'hrms.accident'
    _rec_name = 'accident_sequence_id'

    # --------------------------------------------------------------------------
    # Main details
    accident_sequence_id = fields.Char(readonly=True, index=True,
                                       default=lambda self: _('WA-XXXX'))

    @api.model
    def create(self, vals):
        if vals.get('accident_sequence_id', _('WA-XXXX')) == _('WA-XXXX'):
            vals['accident_sequence_id'] = (self.env['ir.sequence'].next_by_code('accident.code.sequence')
                                            or _('WA-XXXX'))
        result = super(WorkAccident, self).create(vals)
        return result

    employee_id = fields.Many2one('hr.employee',
                                  string='Employee')
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 related='employee_id.company_id',
                                 readonly=True)
    job_id = fields.Many2one('hr.job',
                             string='Job Position',
                             related='employee_id.job_id',
                             readonly=True)
    department_id = fields.Many2one('hr.department',
                                    string='Department',
                                    related='employee_id.department_id',
                                    readonly=True)
    manager_id = fields.Many2one('hr.employee',
                                 string='Manager',
                                 related='employee_id.parent_id',
                                 readonly=True)
    endorse = fields.Boolean()
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Incident Details
    incident_date = fields.Date('Date and Time of Incident')
    incident_type = fields.Selection([
        ('Injury', 'Injury'),
        ('Illness', 'Illness'),
        ('First Aid', 'First Aid')
    ])
    injured_body_part = fields.Selection([
        ('Head', 'Head'),
        ('Shoulder', 'Shoulder'),
        ('Torso', 'Torso'),
        ('Lower Back', 'Lower Back'),
        ('Lower Extremities', 'Lower Extremities'),
        ('Hand and Fingers', 'Hand and Fingers'),
        ('Multiple Body Parts', 'Multiple Body Parts'),
        ('Other', 'Other')
    ])
    severity = fields.Selection([
        ('Minor', 'Minor'),
        ('Moderate', 'Moderate'),
        ('Fatal', 'Fatal'),
        ('Days away from Work', 'Days away from Work'),
        ('Restricted/Transfer', 'Restricted/Transfer')
    ])
    occurred_in_premises = fields.Boolean()
    location = fields.Char()
    witnesses = fields.Many2many('hr.employee')
    employee_task = fields.Char()
    cause = fields.Char()
    incident_description = fields.Text()
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Other Information
    prepared_by = fields.Many2one('res.users', default=lambda self: self.env.uid,
                                  readonly=True)
    date_prepared = fields.Date('Date', default=date.today(), readonly=True)

    reviewed_by = fields.Many2one('hr.employee')
    date_reviewed = fields.Date('Date')

    reviewer = fields.Many2one('hr.employee')
    date_authorized = fields.Date('Date')
    comments = fields.Text()
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Treatment
    physician = fields.Char('Physician/Care Provider Name')
    physician_address = fields.Char('Address')
    physician_notes = fields.Text('Physician/Care Provider Notes')

    hospital = fields.Char('Facility/Clinic/Hospital Name')
    hospital_address = fields.Char('Address')

    health_care_provider = fields.Char()
    id_number = fields.Char('ID Number')
    credit_usage_for_treatment = fields.Float()
    # --------------------------------------------------------------------------
