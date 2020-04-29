from openerp import models, api, fields
from logging import getLogger


def log(**to_output):
    for key, value in to_output.items():
        getLogger().info("\n\n\n{0}: {1}\n\n".format(key, value))


class CandidateRefuseWizard(models.TransientModel):
    _name = "candidate_refuse.wizard"

    refuse = fields.Char(default="Application Refused. Please choose an Action below")

    @api.multi
    def archive_applicant(self):
        applicant = self.env['hr.applicant'].browse(self._context.get('active_id'))

        return applicant.write({'active': False})

    @api.multi
    def black_listed(self):
        applicant = self.env['hr.applicant'].browse(self._context.get('active_id'))

        blacklist = self.env['hr.candidate.blacklisted'].create({
            'applicant_name': applicant.partner_name,
            'job_position': applicant.job_id.id,
            'recruitment_stage': applicant.stage_id.id,
            'responsible': applicant.user_id.id,
        })

        applicant.write({
            'blacklisted': True,
            'active': False,
            'kanban_state': "blocked"
        })

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.candidate.blacklisted',
            'res_id': int(blacklist.id),
            'view_id': False,
            'target': 'new',
        }

    @api.multi
    def cancel(self):
        return False


class BlockedCandidateWizard(models.TransientModel):
    _name = "blocked.candidate.wizard"

    blocked = fields.Char(default="Applicant Status connat be changed. Applicant is Blocked")

    @api.multi
    def cancel(self):
        return False

    @api.multi
    def force_change(self):
        return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'hr.candidate.blacklisted',
                'view_id': False,
        }


class DuplicateCandidateWizard(models.TransientModel):
    _name = "duplicate.candidate.wizard"

    duplicate = fields.Char(default="Application Not saved. Application has duplicate entry, please review other application")
