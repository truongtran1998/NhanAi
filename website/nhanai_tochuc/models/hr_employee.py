# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, timedelta

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    suckhoe_ids = fields.One2many('hr.suckhoe', 'employee_id', string='Tình trạng sức khỏe')


class HrSuckhoe(models.Model):
    _name = 'hr.suckhoe'

    employee_id = fields.Many2one('hr.employee', 'Nhân viên', index=True, store=True, readonly=False)
    # year = fields.Integer(string='Năm', help='Năm kết luận sức khỏe', default=2023)
    year = fields.Selection(
        string="Năm",
        selection=[('2023', '2023'),
                    ('2024', '2024'),
                    ('2025', '2025'),
                   ('2026', '2026'),
                   ('2027', '2027'),
                   ('2028', '2028'),
                   ('2029', '2029'),
                   ('2030', '2030')])
    name = fields.Char(string='Loại bệnh', required=True, translate=True)