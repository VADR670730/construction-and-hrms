# coding: utf-8
"""
    Module Name: HR Infraction
    Author: John Christian Ardosa
    Company: Agilis Enterprise Solutions
    Date Created: January, 2020
"""

from odoo import models, fields, api, _
from logging import getLogger
from odoo.exceptions import UserError
from datetime import date, datetime


def log(**to_output):
    getLogger().info("\n\n\n{0}\n\n".format(to_output))


class InheritEmployeeInfractions(models.Model):
    _inherit = 'hr.employee'

    infraction_ids = fields.One2many(
        'hr.infraction', 'emp_id',
        string="Infractions",
        compute='_compute_infraction_record',
        track_visibility='onchange'

    )

    @api.depends('children')
    def _compute_infraction_record(self):
        for rec in self:
            record = self.env['hr.infraction'].search([('emp_id', '=', rec.id)])
            rec.update({
                'infraction_ids': [(6, 0, record.ids)],
            })


class Infractions(models.Model):
    """Main Model of Infractions which houses the fields
    responsible for the main form and tree view
    """
    _name = "hr.infraction"
    _rec_name = "infraction_sequence_id"
    _description = "Infractions Management"
    _inherit = ["mail.thread", "mail.activity.mixin", "resource.mixin"]

    infraction_sequence_id = fields.Char(string='Infraction ID', required=True, copy=False, readonly=True,
                                         index=True, default=lambda self: _('New'))

    emp_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        track_visibility="onchange",
        required=True,
        help='Select employee who committed the violation'
    )
    job_id = fields.Many2one(
        "hr.job",
        string="Job",
        related="emp_id.job_id",
        readonly=True,
        store=True,
    )
    manager_id = fields.Many2one("hr.employee",
                                 string="Manager",
                                 related="emp_id.parent_id",
                                 readonly=True,
                                 store=True,
                                 )
    department_id = fields.Many2one('hr.department',
                                    string="Department",
                                    related='emp_id.department_id',
                                    readonly=True,
                                    store=True
                                    )

    violation_id = fields.Many2one("hr.company.violation",
                                   string="Violation",
                                   track_visibility="onchange",
                                   required=True,
                                   help='Choose a from past violations or create a new one.'
                                   )

    policy_violated_ids = fields.Many2many("hr.company.policy", string="Policies Violated",
                                           compute='_compute_policy_violated_ids', help="FOR POLICY VIOLATED ID DOMAIN PURPOSES ONLY")

    offense_code_id = fields.Many2one('hr.company.offense', string='Offense Code',
                                      related='policy_violated_id.offense_code_id',
                                      readonly=True,
                                      store=True,
                                      )

    policy_violated_id = fields.Many2one(
        "hr.company.policy",
        string="Policies Violated",
        track_visibility="onchange",
        domain="[('id', 'in', policy_violated_ids)]",
        required=True,
        help='Field shows policies violated by the given violation'
    )

    frequency = fields.Char(
        string="Frequency",
        track_visibility="onchange",
        compute='compute_policy_violation_instance',
        store=True,
        help='Shows how many times an employee has violated a specific Policy. \
        Helps with deciding what corrective action to use for offending employee'
    )

    violation_date = fields.Date(
        string="Date of Violation",
        track_visibility="onchange",
        required=True,
        default=fields.Date.today()
    )

    parent_infraction_id = fields.Many2one(
        'hr.infraction', string="Parent Infraction")
    is_parent = fields.Boolean(string="Is Parent",
                               readonly=True
                               )
    is_child = fields.Boolean(string="Is Child",
                              readonly=True
                              )

    @api.onchange('parent_infraction_id')
    def set_related_infraction(self):
        for rec in self:
            if rec.parent_infraction_id:
                rec.emp_id = rec.parent_infraction_id.emp_id
                rec.violation_id = rec.parent_infraction_id.violation_id
                rec.violation_date = rec.parent_infraction_id.violation_date
                rec.violation_details = rec.parent_infraction_id.violation_details

    @api.constrains('parent_infraction_id')
    def check_parent_infraction(self):
        for rec in self:
            if rec.parent_infraction_id.id == self.id:
                raise UserError(_('Cannot assign record as its own parent'))

    state = fields.Selection(
        string="Case Status",
        selection=[
            ("draft", "Draft"),
            ("open", "Open"),
            ("in_progress", "In Progress"),
            ("for_closure", "For Case Closure"),
            ("closed", "Closed"),
        ],
        default="draft",
    )
    corrective_action = fields.Many2one(
        "hr.infraction.action_history",
        string="Corrective Action",
        compute="get_corrective_action",
        readonly=True,
    )

    violation_details = fields.Text(
        string="How Did It Occur?", required=True, track_visibility="onchange"
    )
    history_ids = fields.One2many(
        "hr.infraction.action_history",
        "infraction_id",
        string="Action History",
        track_visibility="onchange",
        ondelete='cascade'
    )

    suspension_history_ids = fields.One2many('suspension.history','infraction_id',string="Suspension History",
    )

    @api.depends('history_ids')
    def get_corrective_action(self):
        for record in self:
            history_line = record.history_ids.ids
        if history_line:
            self.update({
                'corrective_action': history_line[-1]
            })
        return True

    @api.multi
    def unlink(self):
        """
        Deletes the action history records related to infraction upon the latter's deletion
        """
        for rec in self:
            action_history = self.env['hr.infraction.action_history'].search(
                [('infraction_id', '=', rec.id)])
            for i in action_history:
                i.unlink()
        for i in self.env['hr.infraction.action_history'].browse(self.ids):
            i.unlink()
        result = super(Infractions, self).unlink()

        return result
    
    """ Function Used to auto update action history of all Infraction Records. No longer used """
    # @api.depends('history_ids')
    # def _auto_fill_history(self):
    #     for rec in self:
    #         result = self.env['hr.infraction.action_history'].search(
    #             []).filtered(lambda x: x.infraction_id.id == rec.id).ids
    #         rec.update({'history_ids': [(6, 0, result)]})

    """============================================================================================
        STATE BUTTON FIELDS
       ============================================================================================"""
    date_opened = fields.Date(string="Date Opened",
                              track_visibility='onchange'
                              )
    date_in_progress = fields.Date(string="Date In Progress",
                                   track_visibility='onchange'
                                   )
    date_for_closure = fields.Date(string="Date For Closure",
                                   track_visibility='onchange'
                                   )
    date_closed = fields.Date(string="Date Closed",
                              track_visibility='onchange')
    set_open_by = fields.Many2one('res.users', string="Set to Open By",
                                  track_visibility='onchange'
                                  )
    set_in_progress_by = fields.Many2one('res.users', string="Set to In Progress By",
                                         track_visibility='onchange'
                                         )
    set_for_closure_by = fields.Many2one('res.users', string="Set to For Closure By",
                                         track_visibility='onchange'
                                         )
    set_closed_by = fields.Many2one('res.users', string="Set to Closed By",
                                    track_visibility='onchange'
                                    )
    # ============================================================================================

    @api.multi
    def get_offense_history(self):
        emp_domain = [('emp_id', '=', self.emp_id.id),
                      ('policy_violated_id', 'in', self.policy_violated_ids.ids)]

        return {
            'name': _('Violations for {}'.format(self.emp_id.name)),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.infraction',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': emp_domain,
        }

    @api.model
    def create(self, vals):
        """ Old Code for autosequence upon record creation"""
        # if vals.get('infraction_sequence_id', _('New')) == _('New'):
        #     vals['infraction_sequence_id'] = self.env['ir.sequence'].next_by_code(
        #         'infraction.code.sequence') or _('New')
        if vals.get('infraction_sequence_id', _('New')) == _('New'):
            vals['infraction_sequence_id'] = _('New')
        result = super(Infractions, self).create(vals)

        """ Old code auto creating action history upon creation of record"""
        # self.env['hr.infraction.action_history'].create({
        #     'stage': 'incident_report',
        #     'emp_id': result.emp_id.id,
        #     'infraction_id': result.id,
        #     'offense_code_id': result.offense_code_id.id,
        #     'start_date': result.create_date,
        #     'end_date': result.create_date,
        #     'action_date': result.create_date,
        # })
        return result

    """============================================================================================
        COMPUTES FOR FREQUENCY DEPENDING ON NUMBER OF VIOLATION INSTANCES IN A GIVEN POLICY CODE
       ============================================================================================"""
    @api.depends('emp_id', 'policy_violated_id', 'offense_code_id',)
    def compute_policy_violation_instance(self):
        data = []
        frequency = ""
        for rec in self:
            active_emp_id = rec.emp_id.id if rec.emp_id.id else False
            if active_emp_id:
                record_set = self.env['hr.infraction'].search(
                    [('emp_id', '=', active_emp_id), ('state', '!=', 'closed')])
                for i in record_set:
                    data.append(i.policy_violated_id.id)
                counter = data.count(self.policy_violated_id.id)
                if rec.offense_code_id.corrective_action_ids:
                    for i in rec.offense_code_id.corrective_action_ids:
                        frequency = i.frequencies
                    if rec.offense_code_id and rec.offense_code_id.corrective_action_ids:
                        # getLogger().info("\n\n\nCASE 1 {} {}\n\n\n".format(
                        #     self.offense_code_id, self.offense_code_id.corrective_action_ids))
                        # log(offense_code_id=self.offense_code_id,
                        #     corrective_action=self.offense_code_id.corrective_action_ids)
                        rec.frequency = frequency[counter - 
                                                1 if counter > 0 else counter][1]
                        getLogger().info("\n\n\nCounter{}\nFrequency{}\n\n\n".format(
                            counter-1, frequency))
                    elif counter < 0:
                        getLogger().info("\n\n\nCASE 2\n\n\n")
                        rec.frequency = frequency[0][1]
                    else:
                        getLogger().info("\n\n\nCASE 3\n\n\n")
                        rec.frequency = ""
                    return frequency

    """=============================================================================================
        FOR POLICY VIOLATED ID DOMAIN PURPOSES ONLY
       ============================================================================================"""
    @api.depends('violation_id')
    def _compute_policy_violated_ids(self):
        for record in self:
            record.policy_violated_ids = record.violation_id.policy_violated_ids.ids

    """============================================================================================
        STATE BUTTON FUNCTIONS
       ============================================================================================"""

    @api.multi
    def set_state_inprogress(self):
        self.write({
            'state': 'in_progress',
            'date_in_progress': datetime.now(),
            'set_in_progress_by': self._uid,
            'infraction_sequence_id': self.env['ir.sequence'].next_by_code(
                'infraction.code.sequence') or _('New')
        })
        if self.infraction_sequence_id != _('New'):
            self.env['hr.infraction.action_history'].create({
                'stage': 'incident_report',
                'emp_id': self.emp_id.id,
                'infraction_id': self.id,
                'offense_code_id': self.offense_code_id.id,
                'start_date': self.create_date,
                'end_date': self.create_date,
                'action_date': self.create_date,
            })
        return True
        # self.infraction_sequence_id = self.env['ir.sequence'].next_by_code(
        # 'infraction.code.sequence') or _('New')

    """old code for checking if action history already has stage 'Investigation and NTE Issuance' """
    # @api.multi
    # def set_state_inprogress(self):
    #     for i in self.history_ids:
    #         if i.stage == 'inv_nte_issuance':
    #             self.write({
    #                 'state': 'in_progress',
    #                 'date_in_progress': datetime.now(),
    #                 'set_in_progress_by': self._uid
    #             })
    #             break
    #     else:
    #         raise UserError(
    #             _('Investigation and NTE Issuance should be created in Action History before setting the record in progress'))

    @api.multi
    def set_state_forclosure(self):
        self.write({
            'state': 'for_closure',
            'date_for_closure': datetime.now(),
            'set_for_closure_by': self._uid
        })
        return True

    @api.multi
    def set_state_closed(self):
        self.write({
            'state': 'closed',
            'date_closed': datetime.now(),
            'set_closed_by': self._uid
        })
        return True


"""============================================================================================
    Company Policy houses data of company policies with their corresponding offenses
   ============================================================================================"""


class PolicyCode(models.Model):
    _name = "hr.company.policy"
    _rec_name = "name"
    _description = "Company Policy houses data of company policies with their corresponding offenses"
    _inherit = ["mail.thread", "mail.activity.mixin", "resource.mixin"]

    name = fields.Char(string="Policy Code")
    offense_code_id = fields.Many2one(
        "hr.company.offense", string="Offense Code")
    description = fields.Text(string="Policy Description")


class OffenseCode(models.Model):
    _name = "hr.company.offense"
    _rec_name = "name"

    name = fields.Char(string="Offense Code", size=64)
    corrective_action_ids = fields.One2many(
        "hr.company.offense.frequency",
        'offense_code_id',
        string="Corrective Actions",
    )
    description = fields.Text(string="Offense Code Description")
    frequency = fields.Integer(string="Frequency", compute="_get_frequency")
    corrective_action_enumerate = fields.Text(
        string="Corrective Actions", readonly=True, compute="_get_frequency"
    )

    """============================================================================================
        COMPUTES FOR NUMBER OF CORRECTIVE ACTIONS
       ============================================================================================"""
    @api.depends("corrective_action_ids")
    def _get_frequency(self):
        counter = 0
        list = []
        for i in self:
            corrective_action_ids = i.corrective_action_ids
            for j in corrective_action_ids:
                counter += 1
                list.append(j.action)
            i.frequency = len(i.corrective_action_ids.ids)


"""============================================================================================
    Corrective Action houses Offense Codes that are used for each Company Policy
   ============================================================================================"""


class CorrectiveAction(models.Model):
    _name = "hr.company.offense.frequency"
    _rec_name = "action"
    _description = "Corrective Action houses Offense Codes that are used for each Company Policy"

    frequencies = [
        ("1st_offense", "1st Offense"),
        ("2nd_offense", "2nd Offense"),
        ("3rd_offense", "3rd Offense"),
        ("4th_offense", "4th Offense"),
        ("5th_offense", "5th Offense"),
        ("6th_offense", "6th Offense"),
        ("7th_offense", "7th Offense"),
        ("8th_offense", "8th Offense"),
        ("9th_offense", "9th Offense"),
        ("10th_offense", "10th Offense"),
    ]
    offense_code_id = fields.Many2one(
        "hr.company.offense", string="Offense Code")

    name = fields.Char(string="Offense Frequency",
                       size=64, compute="_get_name", store=True,)

    frequency = fields.Selection(
        string="Offense Frequency", selection=frequencies, required=True
    )

    action = fields.Selection(
        string="Action",
        selection=[
            ("Verbal Warning", "Verbal Warning"),
            ("Written Warning", "Written Warning"),
            ("Suspension", "Suspension"),
            ("Demotion", "Demotion"),
            ("Dismissal", "Dismissal"),
        ],
        required=True,
    )

    @api.depends("frequency")
    def _get_name(self):
        frequencies = self.frequencies
        for i in self:
            if i.frequency == frequencies[0][0]:
                i.name = frequencies[0][1]
            elif i.frequency == frequencies[1][0]:
                i.name = frequencies[1][1]
            elif i.frequency == frequencies[2][0]:
                i.name = frequencies[2][1]
            elif i.frequency == frequencies[3][0]:
                i.name = frequencies[3][1]
            elif i.frequency == frequencies[4][0]:
                i.name = frequencies[4][1]
            elif i.frequency == frequencies[5][0]:
                i.name = frequencies[5][1]
            elif i.frequency == frequencies[6][0]:
                i.name = frequencies[6][1]
            elif i.frequency == frequencies[7][0]:
                i.name = frequencies[7][1]
            elif i.frequency == frequencies[8][0]:
                i.name = frequencies[8][1]
            else:
                i.name = frequencies[9][1]


"""Violation deals with acts committed by offenders which are then assigned
    offense codes based on company policies violated by said act/s"""


class Violation(models.Model):
    _name = "hr.company.violation"
    _inherit = ["mail.thread", "mail.activity.mixin", "resource.mixin"]

    name = fields.Char(string="Violation", size=128)
    description = fields.Text(string="Violation Description")
    policy_violated_ids = fields.Many2many(
        "hr.company.policy", string="Policy Violated"
    )


"""Provides Tree View of Policy and Offense codes commited """


class PolicyOffenseViolationLine(models.Model):
    _name = "hr.company.violation.policy.offense"
    _description = "Provides Tree View of Policy and Offense codes commited"
    _inherit = ["mail.thread", "mail.activity.mixin", "resource.mixin"]

    policy_id = fields.Many2one("hr.company.policy", string="Policy Code")
    offense_id = fields.Many2one(
        "hr.company.offense",
        string="Offense Code",
        readonly=True,
        store=True,
        compute="_get_offense_code",
    )

    @api.depends("policy_id")
    def _get_offense_code(self):
        for record in self:
            record.offense_id = record.policy_id.offense_code_id

    @api.multi
    def name_get(self):
        data = []
        for i in self:
            display_value = "{} - {}".format(i.policy_id.name,
                                             i.offense_id.name)
            data.append((i.id, display_value))
        return data


"""======================Action History===================
   Action stages such as Investigation and Issuance of NTE,
   Collaboration with IMC and Corrective Action are created
   in this model.
   =======================================================
"""


class ActionHistory(models.Model):
    _name = "hr.infraction.action_history"
    _description = "Every corrective action applied to employee for specific violation is recorded here"
    _rec_name = 'corrective_action'
    # _inherit = ["mail.thread","mail.activity.mixin"]
    state = fields.Selection(
        string='State',
        selection=[
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("canceled", "Canceled"),
        ],
        default='draft'
    )

    infraction_id = fields.Many2one(
        "hr.infraction", string="Infraction Record")
    emp_id = fields.Many2one('hr.employee', string="Offending Employee",
                             related='infraction_id.emp_id',
                             readonly=True,
                             store=True
                             )

    stage = fields.Selection(
        string="Stage",
        selection=[
            ("incident_report", "Incident Report"),
            ("inv_nte_issuance", "Investigation and NTE Issuance"),
            ("collaboration", "Collaboration with IMC"),
            ("corrective_action", "Corrective Action"),
        ],
    )
    offense_code_id = fields.Many2one('hr.company.offense', 'Offense Code',
                                      related='infraction_id.offense_code_id',
                                      readonly=True,
                                      store=True
                                      )
    corrective_action = fields.Many2one("hr.company.offense.frequency",
                                        domain="[('offense_code_id', '=', offense_code_id)]",
                                        )
    action = fields.Selection(
        string="Corrective Action",
        related="corrective_action.action",
        readonly=True,
        store=True,
    )
    offense_frequency = fields.Char(
        string="Offense & Frequency",
        compute="_get_default_offense"
    )
    violation_id = fields.Many2one(
        "hr.company.violation",
        string="Violation",
        related='infraction_id.violation_id',
        store=True,
    )
    action_date = fields.Date(string="Action Date", default=fields.Date.today(),
                              help='Date when the action (Incident Report, Investigation and NTE Issuance \
    Collaboration With IMC, and Corrective Action took place'
                              )
    start_date = fields.Date(string="Start Date", default=fields.Date.today())
    end_date = fields.Date(string="End Date", default=fields.Date.today())
    duration = fields.Integer(string="Duration")
    days_remaining = fields.Integer(
        string="Days Remaining",
        compute="_get_remaining_days"
    )
    submit_nte = fields.Boolean(string="Submit NTE")
    attachment = fields.Binary(string="Attachment")
    notes = fields.Text(string="Notes")
    number_of_days = fields.Integer(
        string="Number of Days",
        # compute='_get_number_of_days',
    )
    staggered = fields.Boolean(string="Staggered")
    user_id = fields.Many2one(
        'res.users', string="Current User", compute="get_current_user")
    infraction_state = fields.Selection(
        string='Infraction State', related="infraction_id.state")

    """This method will create a suspension history record 
    #     when an action history suspension record with staggered being False gets created"""
    # @api.model
    # def create(self, vals):
    #     result = super(ActionHistory, self).create(vals)
    #     suspension = self.env['suspension.history']
    #     if result.stage == 'corrective_action' and result.staggered == False:
    #         suspension.create({
    #             'state': 'on_going',
    #             'emp_id': result.emp_id.id,
    #             'action_history_id': result.id,
    #             'infraction_id': result.infraction_id.id,
    #             'date_from': result.start_date,
    #             'date_to': result.end_date,
    #         })
    #     return result

    """ Checks if there are 2 or more instances of incident reports and NTE issuances """
    # @api.constrains('stage')
    # def check_stage_count(self):
    #     for rec in self:
    #         incident_report_count = rec.infraction_id.history_ids.search_count(
    #             [('stage', 'in', ['incident_report']), ('infraction_id.id', '=', rec.infraction_id.id),('infraction_sequence_id','!=',['draft'])])
    #         inv_nte_count = rec.infraction_id.history_ids.search_count(
    #             [('stage', 'in', ['inv_nte_issuance']), ('infraction_id.id', '=', rec.infraction_id.id)])
    #         if incident_report_count > 1:
    #             raise UserError(
    #                 _('Cannot create more than one instance of Incident Report per Record'))
    #         if inv_nte_count > 1:
    #             raise UserError(
    #                 _('Cannot create more than one instance of Investigation and NTE issuance per Record'))

    """Checks if record state is set to In progress before creating Collaboration with IMC stage"""
    @api.constrains('stage')
    def check_record_stage(self):
        for i in self:
            record_state = i.infraction_id.state
            if i.stage == 'collaboration' and record_state != 'in_progress':
                raise UserError(
                    _('Please click Submit button first before creating new Action record with stage Collaboration with IMC.'))

    """Checks start date and end date"""
    # @api.constrains('start_date', 'end_date')
    # def check_start_end_date(self):
    #     for rec in self:
    #         incident_report_start_date = rec.infraction_id.history_ids.search(
    #             [('stage', 'in', ['incident_report']), ('infraction_id.id', '=', rec.infraction_id.id)]).start_date
    #         incident_report_end_date = rec.infraction_id.history_ids.search(
    #             [('stage', 'in', ['incident_report']), ('infraction_id.id', '=', rec.infraction_id.id)]).end_date
    #         # if rec.stage == 'inv_nte_issuance':
    #         if rec.start_date:
    #             if rec.end_date:
    #                 # if rec.start_date < incident_report_end_date:
    #                 #     raise UserError(
    #                 #         _('Start Date of investigation must be after Incident Report End Date'))
    #                 if rec.start_date > rec.end_date:
    #                     raise UserError(
    #                         _('End Date must be later than Start Date'))
    #             else:
    #                 raise UserError(_('End Date must be set.'))
    #         else:
    #             raise UserError(_('Start Date must be set.'))

    """Checks if Infraction has went through Collaboration with IMC stage before creating Corrective Action"""
    # @api.constrains('stage')
    # def check_collab_before_corrective_action(self):
    #     for rec in self.infraction_id.history_ids:
    #         if rec.stage == 'collaboration':
    #             return True
    #     else:
    #         raise UserError(_('Infraction has to undergo Collaboration with IMC stage before applying Corrective Action'))

    """Compute to assign current users id to user_id field """
    @api.depends('infraction_id')
    def get_current_user(self):
        for record in self:
            user_id = record._uid
        self.user_id = user_id

    @api.depends("infraction_id", "stage")
    def _get_default_offense(self):
        code = ""
        for i in self:
            policy_violated_id = i.infraction_id.policy_violated_id
            for j in policy_violated_id:
                code = j.offense_code_id.name
        frequency = self.infraction_id.frequency
        self.offense_frequency = "{} - {}".format(code, frequency)
        return True

    @api.onchange("start_date", "end_date")
    def _get_duration(self):
        duration = abs((self.end_date - self.start_date)).days if self.end_date and self.start_date and (
            self.end_date - self.start_date).days > 0 else 0

        self.duration = duration

    @api.depends("start_date", "end_date")
    def _get_remaining_days(self):
        for line in self:
            duration = (
                abs((line.end_date - line.start_date)).days
                if line.end_date
                and line.start_date
                and (line.end_date - line.start_date).days > 0
                else 0
            )
            line.days_remaining = (
                abs((line.end_date - date.today())).days
                if line.end_date and line.start_date and (date.today() > line.start_date)
                else duration
            )
        return True

    """gets number of days"""
    # @api.onchange("start_date","end_date")
    # def _get_number_of_days(self):
    #     for line in self:
    #             duration = (
    #             abs((line.end_date - line.start_date)).days
    #             if line.end_date
    #             and line.start_date
    #             and (line.end_date - line.start_date).days > 0
    #             else 0
    #         )
    #     self.number_of_days = duration
    
    

    """This function creates and email form window
        Please note that in order to update the email template for any changes made in code below,
        User must delete the old template located in email.template.tree view called 'Notice to Explain, Send by email'
        Same goes when making changes in mail_template.xml in data folder.
    """
    @api.multi
    def send_nte_email(self):
        """
        This function opens a window to compose an email, with the notice to explain template message loaded by default
        """

        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            """
            Find the email template that we've created in data/mail_template_data.xml
            get_object_reference first needs the module name where the template is build and then the name
            of the email template (the record id in XML).
            """
            template_id = ir_model_data.get_object_reference(
                'hrms_compliance', 'nte_email_template')[1]
        except ValueError:
            template_id = False

        try:
            """
            Load the e-mail composer to show the e-mail template in
            """
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            # Model on which you load the e-mail dialog
            'default_model': 'hr.infraction.action_history',
            'default_res_id': self.ids[0],
            # Checks if we have a template and sets it if Odoo found our e-mail template
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_email': True
        }

        # Will show the e-mail dialog to the user in the frontend
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def approve_record(self):
        """Sets Action History State to Approved"""
        self.write(
            {
                'state': 'approved'
            }
        )
        return True

    @api.multi
    def cancel_record(self):
        """Sets Action History State to Canceled"""
        self.write(
            {
                'state': 'canceled'
            }
        )
        return True
    
    @api.multi
    def unlink(self):
        """This method will unlink/delete suspension history record associated with the action history.
        So when an action history with a normal/staggered suspension gets deleted, its respective suspension history
        will get deleted as well
        """
        for recs in self.env['suspension.history'].search([('action_history_id','=',self.id)]):
            recs.unlink()
        result = super(ActionHistory, self).unlink()
        return result

"""========================SUSPENSION HISTORY=======================
        ALL INSTANCES OF EMPLOYEE SUSPENSION IS RECORDED HERE
        THIS MAY BE USED FOR PAYROLL AND TIMEKEEPING PURPOSES
   =================================================================
"""


class SuspensionHistory(models.Model):
    _name = 'suspension.history'
    _description = 'Staggered Suspension History Model'
    _rec_name = 'infraction_id'
    _inherit = ["mail.thread", "mail.activity.mixin", "resource.mixin"]

    status = [
        ('on_going', 'On Going'),
        ('completed', 'Completed')
    ]

    action_history_id = fields.Many2one('hr.infraction.action_history',string="Action History")
    emp_id = fields.Many2one('hr.employee', string="Offending Employee")
    infraction_id = fields.Many2one(
        'hr.infraction', string="Infraction Record")
    used_days = fields.Integer(string="Used Days")
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    duration = fields.Integer(string="Duration", compute="_get_duration")
    remaining_days = fields.Integer(string="Remaining Days", compute="_get_remaining_days")
    state = fields.Selection(
        string='Status',
        selection=status,
        compute='compute_state'
    )

    contract_id = fields.Many2one(
        'hr.contract', string='Current Contract',
        related='emp_id.contract_id',
        readonly=True,
        store=True
    )

    @api.onchange("date_from", "date_to")
    def _get_duration(self):
        for rec in self:
            duration = (
                abs((rec.date_from - rec.date_to)).days + 1
                if rec.date_from
                and rec.date_to
                # and (rec.date_to - rec.date_from).days > 0
                else 0
            )
            rec.duration = duration
    
    @api.depends("date_from","date_to")
    def _get_remaining_days(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                remaining_days = (rec.date_to - date.today()).days
                getLogger().info('\n\n\n{}\n{}\n\n\n'.format(rec.date_to, rec.date_to - date.today()))
                rec.remaining_days = remaining_days

    @api.depends('date_from','date_to','remaining_days')
    def compute_state(self):
        for rec in self:
            if rec.remaining_days <= 0:
                rec.remaining_days = 0
                rec.state = 'completed'
            else:
                rec.state = 'on_going'
