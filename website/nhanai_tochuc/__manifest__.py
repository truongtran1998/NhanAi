# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Quan ly ho so nhan vien',
    'version': '1.0',
    'category': 'Human Resources/Employees',
    'summary': 'Quan ly tong the nhan vien',
    'description': "",
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/hr_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
