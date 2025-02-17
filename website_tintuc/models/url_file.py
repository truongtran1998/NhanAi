from odoo import models, fields, api
import base64

class UserUploadFile(models.Model):
    _name = 'user.upload.file'
    _description = 'User Upload File'

    name = fields.Char(string="File Name", required=True)
    file = fields.Binary(string="Upload File", required=True)
    mimetype = fields.Char(string="MIME Type")
    attachment_id = fields.Many2one('ir.attachment', string="Attachment", readonly=True)
    public_url = fields.Char(string="Public Link", compute="_compute_public_url", store=True)

    @api.depends('attachment_id')
    def _compute_public_url(self):
        for record in self:
            if record.attachment_id:
                record.public_url = f"/web/content/{record.attachment_id.id}?download=true"

    def action_upload_file(self):
        """ Khi người dùng nhấn nút 'Upload', file sẽ được lưu vào ir.attachment """
        for record in self:
            if record.file:
                attachment = self.env['ir.attachment'].create({
                    'name': record.name,
                    'type': 'binary',
                    'datas': record.file,
                    'mimetype': record.mimetype or 'application/octet-stream',
                    'public': True,
                })
                record.attachment_id = attachment