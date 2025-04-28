# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Quan ly van ban tran dinh truong',
    'version': '1.0',
    'category': 'Project',
    'summary': 'Quan ly van ban truong dinh tran',
    'description': "",
    'depends': ['project'],
    'data': [
        'security/project_security.xml',
        'security/ir.model.access.csv',
        'views/task_views.xml',
        'views/project_views.xml',
        'wizard/save_ex_report_wizard_view.xml',
        'wizard/project_report_excel_wizard_view.xml',
        'data/reminder_task.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'nhanai_vanban/static/src/js/count_view.js',
        ]
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
