from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class HRMSEmployeeMovement(models.Model):
    _name = "hr.employee.movement"
    _description = "Employee Management"
    _inherit = ["mail.thread", "mail.activity.mixin", "resource.mixin"]


    name = fields.Many2one('hr.employee', "Employee Name", required=True)
    department_id = fields.Many2one('hr.department', "Department",
                                    related="name.department_id")
    job_id = fields.Many2one('hr.job', "Job Position", related="name.job_id")
    movement_type = fields.Selection([
        ('promition', 'Promotion'),
        ('demotion', 'Demotion'),
        ('lateral', 'Lateral Transfer')
        ], string="Movement Type", required=True)
    movement_date = fields.Date("Movement Date",  required=True)
    new_job_id = fields.Many2one('hr.job', 'New Job Position')
    new_department_id = fields.Many2one('hr.department', "New Department")
    new_contract = fields.Many2one('hr.contract', "New Contract")
    contract = fields.Selection([
        ('update_contract', 'Update Contract'),
        ('new_contract', 'New Contract')])

    state = fields.Selection([
        ('draft', 'Draft'),
        ('for_reviewing', 'Waiting to be Review'),
        ('review', 'Reviewed'),
        ('approve', 'Approve'),
    ], string="Status", default="draft", readonly=True, copy=False)

    date_submitted = fields.Date("Date Submitted")
    submitted_by = fields.Many2one('res.users', 'Submitted By')
    date_review = fields.Date("Date Reviewed")
    review_by = fields.Many2one('res.users', 'Reviewed By')
    date_approved = fields.Date("Date Approved")
    approved_by = fields.Many2one('res.users', 'Approved By')

    contract_history_ids = fields.One2many(
        'hr.contract', 'employee_id',
        string="Contract History",
        compute='_compute_contract_history_record'
    )

    @api.depends('movement_type')
    def _compute_contract_history_record(self):
        record = self.env['hr.contract'].search([('employee_id', '=', self.name.id)])
        self.update({
            'contract_history_ids': [(6, 0, record.ids)],
        })

    @api.multi
    def submit(self):
        for rec in self:
            rec.date_submitted = date.today()
            user_id = self.env['res.users'].browse(self._context.get('uid'))
            rec.submitted_by = user_id.id

        return self.write({'state': 'for_reviewing'})

    @api.multi
    def confirm(self):
        for rec in self:
            rec.date_review = date.today()
            user_id = self.env['res.users'].browse(self._context.get('uid'))
            rec.review_by = user_id.id
        return self.write({'state': 'review'})


    @api.multi
    def approve(self):
        for rec in self:
            if rec.new_job_id:
                previous_contract = self.env['hr.contract'].search([('employee_id','=',rec.name.id),
                                                                    ('state', '=', 'open')])

                if previous_contract:
                    previous_contract = previous_contract[0]

                    previous_contract.write({
                        'date_end': date.today(),
                        'state': 'close',
                        'reason_changing': dict(rec._fields['movement_type'].selection).get(rec.movement_type)
                        })

                    contract = self.env['hr.contract'].create({
                        'name': rec.name.name,
                        'employee_id': rec.name.id,
                        'job_id': rec.new_job_id.id,
                        'department_id': rec.department_id.id,
                        'date_start': date.today(),
                        'date_created': date.today(),
                        'wage': previous_contract.wage,
                        'state': 'open',
                        'active': True
                    })

                    rec.new_contract = contract.id
                    rec.name.job_id = rec.new_job_id.id
                else:
                    raise ValidationError('Employee Has no contract')
            elif rec.new_department_id:
                previous_contract = self.env['hr.contract'].search([('employee_id','=',rec.name.id),
                                                                    ('state', '=', 'open')])
                if previous_contract:
                    previous_contract = previous_contract[0]
                    if rec.contract == 'update_contract':
                        previous_contract.write({
                            'department_id': rec.new_department_id.id,
                        })
                        rec.name.new_department_id = rec.new_department_id.id
                    else:
                        previous_contract.write({
                            'date_end': date.today(),
                            'state': 'close',
                            'reason_changing': dict(rec._fields['movement_type'].selection).get(rec.movement_type)
                            })

                        contract = self.env['hr.contract'].create({
                            'name': rec.name.name,
                            'employee_id': rec.name.id,
                            'job_id': rec.job_id.id,
                            'department_id': rec.new_department_id.id,
                            'date_start': date.today(),
                            'date_created': date.today(),
                            'wage': previous_contract.wage,
                            'state': 'open',
                            'active': True
                        })

                        rec.new_contract = contract.id
                        rec.name.new_department_id = rec.new_department_id.id

                else:
                    raise ValidationError('Employee Has no contract')

            rec.date_approved = date.today()
            user_id = self.env['res.users'].browse(self._context.get('uid'))
            rec.approved_by = user_id.id

        return self.write({'state': 'approve'})
