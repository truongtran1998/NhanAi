from odoo import http
from odoo.http import request

class FileDownloadController(http.Controller):

    @http.route('/download/excel_report', type='http', auth='user')
    def download_excel_report(self, file_path, **kwargs):
        # Đọc file từ đường dẫn tạm
        try:
            with open(f'/tmp/{file_path}', 'rb') as f:
                file_data = f.read()
        except FileNotFoundError:
            return request.not_found()

        # Trả về file trực tiếp
        return request.make_response(
            file_data,
            headers=[
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', f'attachment; filename="{file_path.split("/")[-1]}"'),
            ]
        )