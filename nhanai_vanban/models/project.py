# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import models, fields, api, _, _lt
from odoo.osv import expression
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError, RedirectWarning

class ProjectProject(models.Model):
    _inherit = "project.project"
    loai_van_ban = fields.Selection([
        ('den', 'Đến'),
        ('di', 'Đi'),
        ('noibo', 'Nội bộ'),
        ('quyetdinh', 'Quyết định')], string='Loại văn bản',
        copy=False,
        store=True, tracking=True,default='den')



class Task(models.Model):
    _inherit = "project.task"

    @api.depends('parent_id.project_id', 'display_project_id')
    def _compute_project_id(self):
        for task in self:
            if task.parent_id:
                task.display_project_id = task.project_id
    so_luong_xem = fields.Integer(string="Số lượt xem", readonly=True)
    loai_van_ban = fields.Selection(related='project_id.loai_van_ban',readonly=True, tracking=True)
    ngay_cong_van_den = fields.Datetime('Ngày công văn đến', tracking=True)
    so_den = fields.Integer('Số đến', tracking=True)
    co_quan_ban_hanh = fields.Selection([
        ('byt', 'Bộ Y Tế'),
        ('soyte', 'Sở Y Tế'),
        ('cucpc', 'Cục Phòng Chống HIV/AIDS'),
        ('cucql', 'Cục Quản Lý Khám chữa bệnh'),
        ('dvk', 'Các Đơn Vị Khác')], string='Cơ quan ban hành',
        copy=False, index=True,
        store=True, tracking=True,
        )
    ky_hieu_cong_van = fields.Char('Số/Ký hiệu văn bản', tracking=True)

    ngay_van_ban = fields.Date('Ngày văn bản', tracking=True)
    khoa_phong_text = fields.Boolean(string="Khoa/Phòng nhập tay")
    department_id = fields.Many2one(
        'hr.department', string='Khoa/Phòng thực hiện', tracking=True)
    department_text = fields.Char('Khoa/Phòng thực hiện', tracking=True)
    department_ids = fields.Many2many(
        'hr.department', string='Khoa/Phòng phối hợp', tracking=True)
    department_texts = fields.Char('Khoa/Phòng phối hợp', tracking=True)
    phan_loai_van_ban = fields.Selection([
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
        ('d', 'D'),
        ('e', 'E')], string='Phân loại văn bản',
        copy=False, index=True,
        store=True, tracking=True,
        )
    # van ban di
    nguoi_ky = fields.Char("Người ký", tracking=True) # văn bản đi, quyết đinh, nội bộ
    #
    noi_nhan = fields.Char(string='Nơi nhận văn bản', tracking=True) # văn bản đi, nội bộ
    noi_luu_tru = fields.Char(string='Nơi lưu', tracking=True) # văn bản đi, nội bộ
    #
    so_luong = fields.Integer('Số lượng bản', tracking=True) # văn bản đi
    # van ban noi bo va so quyet dinh
    don_vi_soan_thao = fields.Char(string="Đơn vị soạn thảo", tracking=True)

    is_reminder_created = fields.Boolean(
        string='Tạo lịch nhắc',
        default=False,copy=False,
    )

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('ky_hieu_cong_van', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def increment_view_count(self, recordId, modelName):
        if modelName == "project.task" and recordId:
            task = self.env['project.task'].browse(recordId)
            if task:
                so_luong_xem = task.so_luong_xem + 1
                task.write({'so_luong_xem': so_luong_xem})

    def create_deadline_reminder(self):
        """Tạo lịch nhắc nhở cho các nhiệm vụ bị trễ deadline một lần duy nhất"""
        overdue_tasks = self.search([
            ('date_deadline', '<', fields.Date.today()),  # Deadline đã trễ
            ('stage_id.fold', '=', False),  # Chưa hoàn thành
            ('is_reminder_created', '=', False),  # Chưa tạo nhắc nhở
        ])
        for task in overdue_tasks:
            if task.project_id.loai_van_ban == 'den':
                for user in task.user_ids:
                    # Tạo sự kiện nhắc nhở trong Calendar
                    self.env['mail.activity'].create({
                        'res_model_id': self.env['ir.model']._get('project.task').id,  # Mô hình gắn với activity
                        'res_id': task.id,  # ID của nhiệm vụ
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,  # Loại hoạt động
                        'summary': f"Thông báo đã trễ hạn: {task.name}",
                        'note': f"Công văn: '{task.name}' đã trễ hạn! Ngày phải phản hồi là: {task.date_deadline}.",
                        'date_deadline': fields.Date.today(),
                        'user_id': user.id,  # Giao cho người chịu trách nhiệm
                    })
                # Đánh dấu nhiệm vụ đã được tạo nhắc nhở
                task.is_reminder_created = True
        return True
