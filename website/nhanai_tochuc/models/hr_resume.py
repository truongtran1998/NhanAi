# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ResumeLine(models.Model):
    _inherit = 'hr.resume.line'

    ma_so = fields.Char(string='Số bằng,chứng chỉ', required=True, translate=True)
    so_tiet = fields.Integer('Số tiết', default=0)
    ngay_ra_quyet_dinh = fields.Date(string="Ngày ra quyết định", tracking=True)
    employee_id = fields.Many2one('hr.employee', 'Nhân viên', index=True, store=True, readonly=False)
