# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
import xlsxwriter
import io
import base64
import itertools
from odoo.exceptions import ValidationError



class project_report(models.TransientModel):
    _name = 'project.report.excel'
    _description = "Báo cáo công văn"

    start_date = fields.Date(string="Ngày bắt đầu",required=True)
    end_date = fields.Date(string="Ngày kết thúc",required=True)

    project_id = fields.Many2one('project.project',string="Lựa chọn báo cáo",required=True)


    # def generate_pdf_report(self):
    #
    #     if self.start_date > self.end_date:
    #         raise ValidationError(_("Lỗi! Ngày bắt đầu phải nhỏ hơn ngày kết thúc."))
    #     else:
    #         data_dict = {'id': self.id, 'start_date': self.start_date, 'end_date': self.end_date,
    #                      'employee_ids': self.employee_ids}
    #
    #         return self.env.ref('bi_employee_timesheet_report.timesheet_report_id').report_action(self,
    #                                                                                               data=data_dict)

    def generate_excel_report(self):

        if self.start_date > self.end_date:
            raise ValidationError(_("Lỗi! Ngày bắt đầu phải nhỏ hơn ngày kết thúc."))
        else:
            self.ensure_one()
            project = self.env['project.project'].browse(self.project_id.id)
            if project and project.loai_van_ban == 'den':
                file_path = "SỔ VĂN BẢN ĐẾN TỪ NGÀY " + self.start_date.strftime("%d-%m-%Y") + " ĐẾN " + self.end_date.strftime("%d-%m-%Y") + '.xlsx'
            elif project and project.loai_van_ban == 'di':
                file_path = "SỔ VĂN BẢN ĐI TỪ NGÀY " + self.start_date.strftime(
                    "%d-%m-%Y") + " ĐẾN " + self.end_date.strftime("%d-%m-%Y") + '.xlsx'
            elif project and project.loai_van_ban == 'noibo':
                file_path = "SỔ VĂN BẢN NỘI BỘ TỪ NGÀY " + self.start_date.strftime(
                    "%d-%m-%Y") + " ĐẾN " + self.end_date.strftime("%d-%m-%Y") + '.xlsx'
            else:
                file_path = "SỔ QUYẾT ĐỊNH TỪ NGÀY " + self.start_date.strftime(
                    "%d-%m-%Y") + " ĐẾN " + self.end_date.strftime("%d-%m-%Y") + '.xlsx'
            workbook = xlsxwriter.Workbook('/tmp/' + file_path)

            title_format = workbook.add_format(
                {'border': 1, 'bold': True, 'valign': 'vcenter', 'align': 'center', 'font_size': 11,
                 'bg_color': '#D8D8D8'})

            formate_1 = workbook.add_format({'font_name':'Times New Roman','bold': True, 'align': 'center', 'font_size': 11, 'font_color': 'red'})
            if project and project.loai_van_ban == 'den':
                record = self.env['project.task'].search(
                    [('project_id', '=', self.project_id.id), ('ngay_van_ban', '>=', self.start_date),
                     ('ngay_van_ban', '<=', self.end_date)], order="so_den ASC")

                sheet = workbook.add_worksheet('Report')
                sheet.set_row(3, 25)
                sheet.set_row(6, 30)
                sheet.set_column('A:A', 10)
                sheet.set_column('B:B', 15)
                sheet.set_column('D:F', 25)
                sheet.set_column('C:C', 10)
                sheet.set_column('G:G', 35)
                sheet.set_column('H:Q', 25)
                # title
                left1 = workbook.add_format({'font_name':'Times New Roman','align': 'center', 'bold': True})
                left2 = workbook.add_format({'font_name':'Times New Roman','align': 'center', 'bold': True, 'underline': True})
                sheet.merge_range(0, 0, 0, 3, "SỞ Y TẾ TP HCM", left1)
                sheet.merge_range(1, 0, 1, 3, "BỆNH VIỆN NHÂN ÁI", left2)
                right1 = workbook.add_format({'font_name':'Times New Roman','align': 'center', 'bold': True})
                right2 = workbook.add_format({'font_name':'Times New Roman','align': 'center', 'bold': True, 'underline': True})
                sheet.merge_range(0, 6, 0, 10, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", right1)
                sheet.merge_range(1, 6, 1, 10, "Độc lập - Tự do - Hạnh phúc", right2)
                center = workbook.add_format({'font_name':'Times New Roman','align': 'center', 'bold': True})
                sheet.merge_range(3, 0, 3, 10, "SỔ VĂN BẢN ĐẾN TỪ NGÀY " + self.start_date.strftime("%d/%m/%Y") + " ĐẾN " + self.end_date.strftime("%d/%m/%Y"), center)
                # end title
                border = workbook.add_format({'font_name':'Times New Roman','align': 'center', 'bold': True, 'border': 1})
                border.set_align('vcenter')
                sheet.merge_range(5, 0, 6, 0, "STT", border)
                sheet.merge_range(5, 1, 6, 1, "NGÀY ĐẾN", border)
                sheet.merge_range(5, 2, 6, 2, "SỐ ĐẾN", border)
                sheet.merge_range(5, 3, 6, 3, "CƠ QUAN BAN HÀNH", border)
                sheet.merge_range(5, 4, 6, 4, "KÝ HIỆU VĂN BẢN", border)
                sheet.merge_range(5, 5, 6, 5, "NGÀY VĂN BẢN", border)
                sheet.merge_range(5, 6, 6, 6, "TRÍCH YẾU NỘI DUNG", border)
                sheet.merge_range(5, 7, 6, 7, "KHOA/ PHÒNG THỰC HIỆN", border)
                sheet.merge_range(5, 8, 6, 8, "KHOA/ PHÒNG PHỐI HỢP", border)
                sheet.merge_range(5, 9, 6, 9, "PHÂN LOẠI VĂN BẢN", border)
                sheet.merge_range(5, 10, 6, 10, "THỜI HẠN BÁO CÁO/THỜI HẠN THỰC HIỆN", border)
                sheet.merge_range(5, 11, 5, 14, "TIẾN ĐỘ GIẢI QUYẾT VĂN BẢN", border)
                sheet.merge_range(5, 15, 6, 15, "ĐÁNH GIÁ TIẾN ĐỘ THỰC HIỆN", border)

                sheet.write(6, 11, "NGÀY/ THÁNG/ NĂM THỰC HIỆN BÁO CÁO/TRẢ LỜI", border)
                sheet.write(6, 12, "SỐ/ KÝ HIỆU VB BÁO CÁO/ TRẢ LỜI", border)
                sheet.write(6, 13, "SỐ/ KÝ HIỆU VB XÂY DỰNG TRIỂN KHAI NỘI BỘ", border)
                sheet.write(6, 14, "KHÁC( HỌP, TT, LẬP DS, LƯU....)", border)
                # sheet.write(6, 15, "HOÀN THÀNH", border)
                # sheet.write(6, 16, "KHÔNG HOÀN THÀNH", border)

                # data
                content = workbook.add_format({'font_name':'Times New Roman','align': 'center', 'border': 1})
                row = 7
                stt = 1
                if record:
                    for re in record:
                        sheet.write(row, 0, stt, content)
                        sheet.write(row, 1, re.ngay_cong_van_den.strftime("%d-%m-%Y %H:%M:%S") if re.ngay_cong_van_den else "", content)
                        sheet.write(row, 2, re.so_den if re.so_den else "", content)
                        sheet.write(row, 3, dict(re._fields['co_quan_ban_hanh'].selection).get(re.co_quan_ban_hanh) if re.co_quan_ban_hanh else "", content)
                        sheet.write(row, 4, re.ky_hieu_cong_van if re.ky_hieu_cong_van else "", content)
                        sheet.write(row, 5, re.ngay_van_ban.strftime("%d-%m-%Y") if re.ngay_van_ban else "", content)
                        sheet.write(row, 6, re.name if re.name else "", content)
                        sheet.write(row, 7, re.department_text if re.khoa_phong_text else re.department_id.name, content)
                        department_text = ""
                        for de in re.department_ids:
                            if de.name:
                                department_text = department_text + de.name + ","
                        sheet.write(row, 8, re.department_texts if re.khoa_phong_text else department_text, content)
                        sheet.write(row, 9, dict(re._fields['phan_loai_van_ban'].selection).get(re.phan_loai_van_ban) if re.phan_loai_van_ban else "",
                                    content)
                        sheet.write(row, 10, re.date_deadline.strftime("%d-%m-%Y") if re.date_deadline else "", content)
                        for sub in re.child_ids:
                            if sub and sub.project_id.loai_van_ban == 'di':
                                ngay_thuc_hien_tra_loi = sub.ngay_van_ban
                                ky_hieu_cong_van_tra_loi = sub.ky_hieu_cong_van
                                sheet.write(row, 11, ngay_thuc_hien_tra_loi.strftime("%d-%m-%Y") if ngay_thuc_hien_tra_loi else "", content)
                                sheet.write(row, 12, ky_hieu_cong_van_tra_loi if ky_hieu_cong_van_tra_loi else "", content)
                            elif sub and sub.project_id.loai_van_ban == 'noibo':
                                ngay_thuc_hien_tra_loi = sub.ngay_van_ban
                                ky_hieu_cong_van_tra_loi = sub.ky_hieu_cong_van
                                sheet.write(row, 11, ngay_thuc_hien_tra_loi.strftime("%d-%m-%Y") if ngay_thuc_hien_tra_loi else "", content)
                                sheet.write(row, 13, ky_hieu_cong_van_tra_loi if ky_hieu_cong_van_tra_loi else "",content)
                            else:
                                sheet.write(row, 11, "", content)
                                sheet.write(row, 12, "", content)
                                sheet.write(row, 13, "", content)
                        sheet.write(row, 14, "", content)
                        sheet.write(row, 15, re.stage_id.name, content)
                        stt = stt + 1
                        row = row + 1
                else:
                    sheet.merge_range(row, 0, row +  7, 14, "Không có công văn, chứng từ nào trong khoảng thời gian bạn chọn.", formate_1)

            elif project and project.loai_van_ban == 'di':
                record = self.env['project.task'].search(
                    [('project_id', '=', self.project_id.id), ('ngay_van_ban', '>=', self.start_date),
                     ('ngay_van_ban', '<=', self.end_date)])
                sheet = workbook.add_worksheet('Report')
                sheet.set_row(3, 25)
                sheet.set_row(6, 30)
                sheet.set_column('A:A', 10)
                sheet.set_column('B:C', 15)
                sheet.set_column('D:D', 25)
                sheet.set_column('F:G', 20)
                sheet.set_column('H:I', 15)
                # title
                left1 = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'bold': True})
                left2 = workbook.add_format(
                    {'font_name': 'Times New Roman', 'align': 'center', 'bold': True, 'underline': True})
                sheet.merge_range(0, 0, 0, 3, "SỞ Y TẾ TP HCM", left1)
                sheet.merge_range(1, 0, 1, 3, "BỆNH VIỆN NHÂN ÁI", left2)
                right1 = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'bold': True})
                right2 = workbook.add_format(
                    {'font_name': 'Times New Roman', 'align': 'center', 'bold': True, 'underline': True})
                sheet.merge_range(0, 6, 0, 10, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", right1)
                sheet.merge_range(1, 6, 1, 10, "Độc lập - Tự do - Hạnh phúc", right2)
                center = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'bold': True})
                sheet.merge_range(3, 0, 3, 10, "SỔ VĂN BẢN ĐI TỪ NGÀY " + self.start_date.strftime(
                    "%d/%m/%Y") + " ĐẾN " + self.end_date.strftime("%d/%m/%Y"), center)
                # end title
                border = workbook.add_format(
                    {'font_name': 'Times New Roman', 'align': 'center', 'bold': True, 'border': 1})
                border.set_align('vcenter')
                sheet.write(5, 0, "STT", border)
                sheet.write(5, 1, "Số/ký hiệu", border)
                sheet.write(5, 2, "Ngày văn bản", border)
                sheet.write(5, 3, "Trích yếu nội dung", border)
                sheet.write(5, 4, "Người ký", border)
                sheet.write(5, 5, "Nơi nhận văn bản", border)
                sheet.write(5, 6, "Nơi lưu", border)
                sheet.write(5, 7, "Số lượng bản", border)
                sheet.write(5, 8, "Ghi chú", border)
                # data
                content = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'border': 1})
                row = 6
                stt = 1
                if record:
                    for re in record:
                        sheet.write(row, 0, stt, content)
                        sheet.write(row, 1, re.ky_hieu_cong_van if re.ky_hieu_cong_van else "", content)
                        sheet.write(row, 2, re.ngay_van_ban.strftime("%d-%m-%Y") if re.ngay_van_ban else "", content)
                        sheet.write(row, 3, re.name if re.name else "", content)
                        sheet.write(row, 4, re.nguoi_ky if re.nguoi_ky else "", content)
                        sheet.write(row, 5, re.noi_nhan if re.noi_nhan else "", content)
                        sheet.write(row, 6, re.noi_luu_tru if re.noi_luu_tru else "", content)
                        sheet.write(row, 7, re.so_luong if re.so_luong else "", content)
                        stt = stt + 1
                        row = row + 1
                else:
                    sheet.merge_range(row, 0, row + 7, 14,
                                      "Không có công văn, chứng từ nào trong khoảng thời gian bạn chọn.", formate_1)

            elif project and project.loai_van_ban == 'noibo':
                record = self.env['project.task'].search(
                    [('project_id', '=', self.project_id.id), ('ngay_van_ban', '>=', self.start_date),
                     ('ngay_van_ban', '<=', self.end_date)])
                sheet = workbook.add_worksheet('Report')
                sheet.set_row(3, 25)
                sheet.set_row(6, 30)
                sheet.set_column('A:A', 10)
                sheet.set_column('B:C', 15)
                sheet.set_column('D:D', 25)
                sheet.set_column('E:H', 15)
                # title
                left1 = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'bold': True})
                left2 = workbook.add_format(
                    {'font_name': 'Times New Roman', 'align': 'center', 'bold': True, 'underline': True})
                sheet.merge_range(0, 0, 0, 3, "SỞ Y TẾ TP HCM", left1)
                sheet.merge_range(1, 0, 1, 3, "BỆNH VIỆN NHÂN ÁI", left2)
                right1 = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'bold': True})
                right2 = workbook.add_format(
                    {'font_name': 'Times New Roman', 'align': 'center', 'bold': True, 'underline': True})
                sheet.merge_range(0, 6, 0, 10, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", right1)
                sheet.merge_range(1, 6, 1, 10, "Độc lập - Tự do - Hạnh phúc", right2)
                center = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'bold': True})
                sheet.merge_range(3, 0, 3, 10, "SỔ VĂN BẢN NỘI BỘ TỪ NGÀY " + self.start_date.strftime(
                    "%d/%m/%Y") + " ĐẾN " + self.end_date.strftime("%d/%m/%Y"), center)
                # end title
                border = workbook.add_format(
                    {'font_name': 'Times New Roman', 'align': 'center', 'bold': True, 'border': 1})
                border.set_align('vcenter')
                sheet.write(5, 0, "STT", border)
                sheet.write(5, 1, "Số/ký hiệu", border)
                sheet.write(5, 2, "Ngày văn bản", border)
                sheet.write(5, 3, "Trích yếu nội dung", border)
                sheet.write(5, 4, "Người ký", border)
                sheet.write(5, 5, "Đơn vị soạn thảo", border)
                sheet.write(5, 6, "Nơi nhận", border)
                sheet.write(5, 7, "Lưu", border)
                # data
                content = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'border': 1})
                row = 6
                stt = 1
                if record:
                    for re in record:
                        sheet.write(row, 0, stt, content)
                        sheet.write(row, 1, re.ky_hieu_cong_van if re.ky_hieu_cong_van else "", content)
                        sheet.write(row, 2, re.ngay_van_ban.strftime("%d-%m-%Y") if re.ngay_van_ban else "", content)
                        sheet.write(row, 3, re.name if re.name else "", content)
                        sheet.write(row, 4, re.nguoi_ky if re.nguoi_ky else "", content)
                        sheet.write(row, 5, re.don_vi_soan_thao if re.don_vi_soan_thao else "", content)
                        sheet.write(row, 6, re.noi_nhan if re.noi_nhan else "", content)
                        sheet.write(row, 7, re.noi_luu_tru if re.noi_luu_tru else "", content)
                        stt = stt + 1
                        row = row + 1
                else:
                    sheet.merge_range(row, 0, row + 7, 14,
                                      "Không có công văn, chứng từ nào trong khoảng thời gian bạn chọn.", formate_1)
            else:
                record = self.env['project.task'].search(
                    [('project_id', '=', self.project_id.id), ('ngay_van_ban', '>=', self.start_date),
                     ('ngay_van_ban', '<=', self.end_date)])
                sheet = workbook.add_worksheet('Report')
                sheet.set_row(3, 25)
                sheet.set_row(6, 30)
                sheet.set_column('A:A', 10)
                sheet.set_column('B:C', 15)
                sheet.set_column('D:D', 25)
                sheet.set_column('E:H', 15)
                # title
                left1 = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'bold': True})
                left2 = workbook.add_format(
                    {'font_name': 'Times New Roman', 'align': 'center', 'bold': True, 'underline': True})
                sheet.merge_range(0, 0, 0, 3, "SỞ Y TẾ TP HCM", left1)
                sheet.merge_range(1, 0, 1, 3, "BỆNH VIỆN NHÂN ÁI", left2)
                right1 = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'bold': True})
                right2 = workbook.add_format(
                    {'font_name': 'Times New Roman', 'align': 'center', 'bold': True, 'underline': True})
                sheet.merge_range(0, 6, 0, 10, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", right1)
                sheet.merge_range(1, 6, 1, 10, "Độc lập - Tự do - Hạnh phúc", right2)
                center = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'bold': True})
                sheet.merge_range(3, 0, 3, 10, "SỔ QUYẾT ĐỊNH TỪ NGÀY " + self.start_date.strftime(
                    "%d/%m/%Y") + " ĐẾN " + self.end_date.strftime("%d/%m/%Y"), center)
                # end title
                border = workbook.add_format(
                    {'font_name': 'Times New Roman', 'align': 'center', 'bold': True, 'border': 1})
                border.set_align('vcenter')
                sheet.write(5, 0, "STT", border)
                sheet.write(5, 1, "Số/ký hiệu", border)
                sheet.write(5, 2, "Ngày văn bản", border)
                sheet.write(5, 3, "Trích yếu nội dung", border)
                sheet.write(5, 4, "Người ký", border)
                sheet.write(5, 5, "Đơn vị soạn thảo", border)
                sheet.write(5, 6, "Nơi nhận", border)
                sheet.write(5, 7, "Lưu", border)
                # data
                content = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'border': 1})
                row = 6
                stt = 1
                if record:
                    for re in record:
                        sheet.write(row, 0, stt, content)
                        sheet.write(row, 1, re.ky_hieu_cong_van if re.ky_hieu_cong_van else "", content)
                        sheet.write(row, 2, re.ngay_van_ban.strftime("%d-%m-%Y") if re.ngay_van_ban else "", content)
                        sheet.write(row, 3, re.name if re.name else "", content)
                        sheet.write(row, 4, re.nguoi_ky if re.nguoi_ky else "", content)
                        sheet.write(row, 5, re.don_vi_soan_thao if re.don_vi_soan_thao else "", content)
                        sheet.write(row, 6, re.noi_nhan if re.noi_nhan else "", content)
                        sheet.write(row, 7, re.noi_luu_tru if re.noi_luu_tru else "", content)
                        stt = stt + 1
                        row = row + 1
                else:
                    sheet.merge_range(row, 0, row + 7, 14,
                                      "Không có công văn, quyết định nào trong khoảng thời gian bạn chọn.", formate_1)

            workbook.close()
            ex_report = base64.b64encode(open('/tmp/' + file_path, 'rb+').read())
            excel_report_id = self.env['save.ex.report.wizard'].create({"document_frame": file_path,
                                                            "file_name": ex_report})

            return {
                'res_id': excel_report_id.id,
                'name': 'Files to Download',
                'view_type': 'form',
                "view_mode": 'form',
                'view_id': False,
                'res_model': 'save.ex.report.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
