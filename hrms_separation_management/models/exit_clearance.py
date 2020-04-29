from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class HRMSExitClearance(models.Model):
    _name = "hr.exit.clearance"
    _description = "Exit Clearance"
    _inherit = ["mail.thread", "mail.activity.mixin", "resource.mixin"]

    decision = fields.Selection([
        ('approve', 'Approved')
    ], string="Status", copy=False, compute="_get_separation_request",
                                store=True)
    note = fields.Text(string="Notes", compute="_get_separation_request",
                       store=True)
    date_of_request = fields.Date("Date Request approval",
                                  compute="_get_separation_request",
                                  store=True)
    name = fields.Many2one('hr.employee', "Employee Name", required=True)
    job_id = fields.Many2one('hr.job', "Position",
                             related="name.job_id")
    separation_type = fields.Selection([
        ('resignation', 'Resignation'),
        ('terminated_company', 'Termination(Company Initiated)'),
        ('terminated_infraction', 'Termination (Infraction)'),
        ('retirement', 'Retirement')
    ], string="Separation Type", compute="_get_separation_request",
                                        store=True)
    joined = fields.Date("Joined Date", compute="_get_separation_request",
                         store=True)
    relieved = fields.Date("Relieved Date", compute="_get_separation_request",
                           store=True)
    date_raised = fields.Date("Date Raised", compute="_get_separation_request",
                              store=True)
    clearance_details = fields.One2many('hr.exit.clearance.lines',
                                        'clearance_id',
                                        string="Clearance Deatils")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('cleared', 'Cleared'),
    ], string="Status", default="draft", readonly=True, copy=False)

    separation_parent_id = fields.Many2one('hr.separation',
                                           'Separation Parent ID',
                                           ondelete="cascade")

    date_submitted = fields.Date("Date Submitted")
    submitted_by = fields.Many2one('res.users', 'Submitted By')
    date_approved = fields.Date("Date Cleared")
    approved_by = fields.Many2one('res.users', 'Cleared By')

    @api.multi
    def unlink(self):
        for i in self:
            if i.separation_parent_id and i.state == 'cleared':
                separation = self.env['hr.separation'].search([
                    ('id', '=', i.separation_parent_id.id)])
                separation.clearance = False
        return super(HRMSExitClearance, self).unlink()

    @api.multi
    def submit(self):
        for rec in self:
            data = []
            rec.date_submitted = date.today()

            user_id = self.env['res.users'].browse(self._context.get('uid'))
            rec.submitted_by = user_id.id

            duplicate = self.search([
                ('name', '=', rec.name.id),
                ('separation_parent_id', '=', rec.separation_parent_id.id),
                ('state', '=', 'pending')
            ])
            if duplicate:
                raise UserError('''Duplicate Exit Clearance.
                                Please Check the other records for Reference''')

            approver = self.env['hr.exit.clearance.approver'].search([
                ('job_id', '=', rec.job_id.id)
            ])

            if approver:
                for i in approver.approve_ids:
                    val = {
                        'name' : i.name.id,
                        'job_id' : i.job_id.id,
                        'department_id' : i.department_id.id,
                    }
                    data.append([0, 0, val])

        return self.write({
            'clearance_details': data,
            'state': 'pending'
        })

    @api.multi
    def clear(self):
        pending = False
        for i in self:
            for rec in i.clearance_details:
                if rec.status == 'pending':
                    pending = True

            if not pending:
                i.date_approved = date.today()
                user_id = self.env['res.users'].browse(self._context.get('uid'))
                i.approved_by = user_id.id
                separation_req = self.env['hr.separation'].search([
                    ('name', '=', self.name.id),
                    ('state', '=', 'approve'),
                    ('clearance', '=', False)
                ])

                if separation_req:
                    separation_req.clearance = True

                return self.write({
                    'state': 'cleared'
                })
            else:
                raise UserError('Employee need to be approved in every Approver below')

    @api.depends('name')
    def _get_separation_request(self):
        for rec in self:
            if rec.name:
                separation_req = rec.env['hr.separation'].search([
                    ('name', '=',rec.name.id),
                    ('state', '=', 'approve'),
                    ('clearance', '=', False)
                ])
                if separation_req:
                    rec.decision = separation_req.state
                    rec.note = separation_req.note
                    rec.date_of_request = separation_req.date_of_request
                    rec.separation_type = separation_req.separation_type
                    rec.joined = separation_req.joined
                    rec.relieved = separation_req.relieved
                    rec.date_raised = separation_req.date_raised
                    rec.separation_parent_id = separation_req.id


class HRMSExitClearanceLines(models.Model):
    _name = "hr.exit.clearance.lines"

    clearance_id = fields.Many2one('hr.exit.clearance', ondelete="cascade")
    name = fields.Many2one('hr.employee', "Name")
    job_id = fields.Many2one('hr.job', "Job Position", related="name.job_id")
    department_id = fields.Many2one('hr.department', "Department",
                                    related="name.department_id")
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved')
    ], string="Status",  default="pending")


class HRMSExitClearanceApprover(models.Model):
    _name = "hr.exit.clearance.approver"
    _rec_name = "job_id"

    job_id = fields.Many2one('hr.job', "Job Position", required=True)
    approve_ids = fields.One2many('hr.exit.clearance.approver.lines',
                                  'approver_id',
                                  string="Clearance Approver")

    @api.constrains('job_id')
    def check_duplicate_true(self):
        for i in self:
            if i.job_id:
                duplicate = self.search([
                    ('job_id', '=', i.job_id.id),
                    ('id', '!=', i.id)
                ])
                if duplicate:
                    raise UserError('''One Department is allowed.
                                    Cannot Create with same Department Approver''')


class HRMSExitClearanceApproverLines(models.Model):
    _name = "hr.exit.clearance.approver.lines"

    approver_id = fields.Many2one('hr.exit.clearance.approver',
                                  ondelete="cascade")
    name = fields.Many2one('hr.employee', "Name")
    job_id = fields.Many2one('hr.job', "Job Position", related="name.job_id")
    department_id = fields.Many2one('hr.department', "Department",
                                    related="name.department_id")
