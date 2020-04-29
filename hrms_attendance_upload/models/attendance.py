# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time as tm
from odoo import api, fields, models, _
from odoo.tools import mute_logger, pycompat
from datetime import date, datetime, timedelta, time
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from dateutil.parser import parse
from dateutil.tz import gettz
from io import StringIO, BytesIO
import base64
import csv

import logging
_logger = logging.getLogger("_name_")

def create_datefrom_parse(original_datetime):
    tzinfos = {"PHT": +800, "CST": gettz("Asia/Manila")}
    dt = parse(original_datetime + "PHT", tzinfos=tzinfos)
    date_new = datetime.strptime('%s-%s-%s %s:%s:%s'%(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second), DT)
    return date_new - timedelta(hours=8)

class HREmployee(models.Model):
    _inherit = "hr.employee"

    biometric = fields.Char(string="Biometric")

    @api.constrains('biometric')
    def _check_biometric(self):
        if self.biometric:
            data = self.search([('biometric', '=', self.biometric), ('id', '!=', self.id)], limit=1)
            if data[:1]:
                raise ValidationError(_("Biometric No. must be a unique per employee."))
class HRAttendance(models.Model):
    _inherit = 'hr.attendance'

    attendance_process_id = fields.Many2one('process.attendance', string="Upload Reference", readonly=True)

class AttendanceFile(models.Model):
    _name = 'attendance.file'

    attendance_process_id = fields.Many2one('process.attendance', string="Process")
    file = fields.Binary(string="Attandance CSV File")
    filename = fields.Char(string="File Name")
    date_uploaded = fields.Datetime(string="Date Upload", default=fields.Datetime.now())

class AttendanceSorting(models.Model):
    _name = 'attendance.sorting'
    _oder = 'attendance_time asc, employee_id'
    _rec_name = 'employee_id'

    attendance_process_id = fields.Many2one('process.attendance', string="Process", ondelete="cascade")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    attendance_time = fields.Datetime(string="Attendance Time")
    attendance_type = fields.Selection([('sign_in', 'Sign In'), ('sign_out', 'Sign Out')], string="Action")
    invalid_data = fields.Boolean("Invalid Attendance Data")

class ProcessAttendance(models.Model):
    _name = 'process.attendance'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']

    @api.multi
    def _get_data_count(self):
        for i in self:
            i.data_count = self.env['attendance.sorting'].search_count([('attendance_process_id', '=', i.id)])
            i.employee_attendance_count = self.env['hr.attendance'].search_count([('attendance_process_id', '=', i.id)])

    name = fields.Char(string="Title", required=True,
                       readonly=True, states={'draft': [('readonly', False)]}, track_visibility="always")
    process_date = fields.Date(string="Process Date", default=fields.Date.today(), readonly=True,
                               states={'draft': [('readonly', False)]}, track_visibility="always")
    attendance_file_ids = fields.One2many('attendance.file', 'attendance_process_id', string="Attendance Files",
                                          readonly=True, states={'draft': [('readonly', False)]})
    attendance_sorting_ids = fields.One2many('attendance.sorting', 'attendance_process_id', string="Uploaded Attendance")
    attendance_record_ids = fields.One2many('hr.attendance', 'attendance_process_id', string="Attendance Record")
    data_count = fields.Float(string="Data Count", compute="_get_data_count")
    employee_attendance_count = fields.Float(string="Employee Attendance Records", compute="_get_data_count")
    state = fields.Selection([
                ('draft', 'Draft'),
                ('sorting', 'Sorting Attandance'),
                ('done', 'Done'),
                ('cancel', 'Cancel')], default='draft',
                string="Status", track_visibility="always")
    error_msg = fields.Text(string="Errors", readonly=True)

    @api.multi
    def push_sorted_attendance(self):
        employee_ids = set([i.employee_id.id for i in self.attendance_sorting_ids])
        attendance_data = []
        error_msg = ''
        for emp in employee_ids:
            attendance = self.env['attendance.sorting'].search([('attendance_process_id', '=', self.id),('employee_id', '=', emp)], order="attendance_time asc")
            current_attendance = self.env['hr.attendance'].search([('employee_id','=', emp), ('check_out', 'in', [False])])
            if attendance[0].attendance_type == 'sign_in' and current_attendance[:1]:
                attendance[0].write({'invalid_data': False})
                error_msg += '\n%s has already a Sign In record (%s) on the attendance database, and you are trying to import attendance record that begins with Sign In action.\n(You may either edit or delete the data in order to proceed)\n'%(attendance[0].employee_id.name, (attendance[0].attendance_time + timedelta(hours=8)).strftime(DT))
            if attendance[0].attendance_type == 'sign_out' and not current_attendance[:1]:
                attendance[0].write({'invalid_data': False})
                error_msg += '\n\n%s attendance must begin with Sign In action\n'%(attendance[0].employee_id.name)
            attendance_pair = {'attendance_process_id': self.id, 'employee_id': emp, 'check_in': False, 'check_out': False}

            if current_attendance[:1]:
                attendance_pair['check_in'] = current_attendance[:1].check_in
            for att in attendance:
                if attendance_pair.get('check_in') and not attendance_pair.get('check_out') and att.attendance_type == 'sign_out':
                    att.write({'invalid_data': False})
                    attendance_pair['check_out'] = att.attendance_time
                elif not attendance_pair.get('check_in') and att.attendance_type == 'sign_in' and not attendance_pair.get('check_out'):
                    att.write({'invalid_data': False})
                    attendance_pair['check_in'] = att.attendance_time
                else:
                    att.write({'invalid_data': True})
                    error_msg += 'Attandance Sign In must be followed by Sign Out record or vice-versa\n'
                if attendance_pair.get('check_in') and attendance_pair.get('check_out'):
                    attendance_data.append([0, 0, attendance_pair])
                    rec = self.env['hr.attendance'].create(attendance_pair)
                    attendance_pair.update({'check_in': False, 'check_out': False})


            #Still record attendance if it end with Sign In
            if attendance_pair.get('check_in') and not attendance_pair.get('check_out'):
                rec = self.env['hr.attendance'].create(attendance_pair)
        # error_msg += '\n\nAttandance Sign In must be followed by Sign Out record or vice-versa'
        for d in attendance_data:
            _logger.info('\n\n\nData: %s\n\n'%(str(d)))
        if error_msg == '':

            self.write({'error_msg': None, 'state': 'done'})
        else: self.write({'error_msg': error_msg})

        return True


    @api.multi
    def process_attendance_file(self):
        for i in self.attendance_file_ids:
            reader_info = []
            csv_data = base64.b64decode(i.file)
            csv_data = csv_data.decode(encoding='ASCII').encode('utf-8')
            csv_iterator = pycompat.csv_reader(
                BytesIO(csv_data),
                delimiter=',',lineterminator='\r\n')
            try:
                reader_info.extend(csv_iterator)
            except Exception:
                raise ValidationError(_("File must be a CSV Format and use 'comma' as a delimeter"))
            keys = reader_info[0]
            del reader_info[0]
            values = {}
            for i in range(len(reader_info)):
                field = reader_info[i]
                values = dict(zip(keys, field))
                if not values.get('Biometric') or not values.get('Attendance Time') or not values.get('Action') or (values.get('Action') and not values.get('Action') in ['sign_in', 'sign_out']):
                    raise ValidationError(_('File must have the following Columns and Data:\n\t1. Biometric\n\t2.Attendance Time\n\t3. Action\n\nAction, must be either "sign_in" or "sign_out".'))
                employee = self.env['hr.employee'].search([('biometric', '=', values.get('Biometric'))], limit=1)
                # _logger.info('\n\n\nEmployee: %s\n\n\n'%(str(values.get('Attendance Time'))))
                if employee[:1]:
                    attendance_time = create_datefrom_parse(values.get('Attendance Time'))
                    dup_count = self.env['attendance.sorting'].search_count([
                                        ('attendance_process_id', '=', self.id),
                                        ('employee_id', '=', employee.id),
                                        ('attendance_time', '=', attendance_time)])
                    if dup_count == 0:
                        self.env['attendance.sorting'].create({
                            'employee_id': employee[:1].id,
                            'attendance_time' : attendance_time,
                            'attendance_type' : values.get('Action'),
                            'attendance_process_id': self.id
                        })
                else: raise ValidationError(_("No matching employee record found owning the biometric no. %s"%(values.get('Biometric'))))
        self.write({'state': 'sorting'})
