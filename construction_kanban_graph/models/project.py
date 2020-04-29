# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime
import json

class Project(models.Model):
    _inherit = "project.project"
    _description = "Project Inherited"

    @api.one
    def _kanban_dashboard_graph(self):
        self.kanban_dashboard_graph = json.dumps(self.get_bar_graph_datas())

    @api.one
    def _kanban_dashboard_line_graph(self):
        self.kanban_dashboard_line_graph = json.dumps(self.get_line_graph_datas())

    kanban_dashboard_graph = fields.Text(compute='_kanban_dashboard_graph')
    kanban_dashboard_line_graph = fields.Text(compute='_kanban_dashboard_line_graph')

    @api.multi
    def get_bar_graph_datas(self):
        datas = [{"value": self.material_budget, "labels":["1.Material","Budget"]},
                 {"value": self.material_expense, "labels":["1.Material","Actual Expense"]},
                 {"value": self.service_budget, "labels":["2.Subcontract...","Budget"]},
                 {"value": self.service_expense, "labels":["2.Subcontract...","Actual Expense"]},
                 {"value": self.labor_budget, "labels":["3.Labor","Budget"]},
                 {"value": self.labor_expense, "labels":["3.Labor","Actual Expense"]},
                 {"value": self.equipment_budget, "labels":["4.Equipment","Budget"]},
                 {"value": self.equipment_expense, "labels":["4.Equipments","Actual Expense"]},
                 {"value": self.overhead_budget, "labels":["5.Overheads","Budget"]},
                 {"value": self.overhead_expense, "labels":["5.Overheads","Actual Expense"]}]
        return [{'values': datas, 'id': self.id}]

    @api.multi
    def get_line_graph_datas(self):
        datas = []
        for project in self.projection_accomplishment_ids:
            pdate = project.date
            if not self.survey_frequent in ['week']:
                datas.append({"value": ((project.projected) / 100), "labels": [pdate.strftime("%b")+" "+pdate.strftime("%Y"),"Projected Accomplishment"]})
                datas.append({"value": ((project.actual) / 100), "labels": [pdate.strftime("%b")+" "+pdate.strftime("%Y"),"Actual Accomplishment"]})
            else:
                week = 'W%s - %s'%(pdate .strftime('%V'), pdate.strftime("%Y"))
                datas.append({"value": ((project.projected) / 100), "labels": [week,"Projected Accomplishment"]})
                datas.append({"value": ((project.actual) / 100), "labels": [week,"Actual Accomplishment"]})
        return [{'values': datas, 'id': self.id}]
