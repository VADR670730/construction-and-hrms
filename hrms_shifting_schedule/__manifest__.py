# -*- coding: utf-8 -*-
{
    "name": "HRMS Shifting Schedule",
    "summary": "Agilis Localized Timekeeping - Filing of shifting schedules",
    "version": "12",
    "author": "Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "category": "Human Resource",
    "depends": [
        'hr',
        'hr_attendance',
        'ducument_approval',
        'web_widget_many2many_tags_multi_selection'],
    "data": [
        # 'security/user_group.xml',
        'security/ir.model.access.csv',
        # 'views/res_config_setting.xml',
        'views/shifting_schedule.xml'
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
}
