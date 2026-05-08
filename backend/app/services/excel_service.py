"""
Excel 生成服务 - 重构版
支持生成 database_element.xlsx
"""
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from datetime import datetime
from typing import List

from ..models.case import CaseData


class ExcelService:
    """Excel 文件生成服务"""

    def generate(self, cases: list, output_path: str):
        """生成案件要素 Excel（旧版兼容）"""
        wb = Workbook()
        ws = wb.active
        ws.title = "案件要素"

        # 表头样式
        header_font = Font(bold=True, size=12)
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font_white = Font(bold=True, size=12, color="FFFFFF")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # 表头
        headers = ["序号", "文件名", "原告", "被告", "案件类型", "标的额", "案件事实", "证据", "受理法院", "状态", "创建时间"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font_white
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = border

        # 数据行
        for row, case in enumerate(cases, 2):
            ws.cell(row=row, column=1, value=row - 1).border = border
            ws.cell(row=row, column=2, value=case.get("filename", "")).border = border
            ws.cell(row=row, column=3, value=case.get("plaintiff", "")).border = border
            ws.cell(row=row, column=4, value=case.get("defendant", "")).border = border
            ws.cell(row=row, column=5, value=case.get("case_type", "")).border = border
            ws.cell(row=row, column=6, value=case.get("amount", "")).border = border
            ws.cell(row=row, column=7, value=case.get("facts", "")).border = border
            ws.cell(row=row, column=8, value="\n".join(case.get("evidence", []))).border = border
            ws.cell(row=row, column=9, value=case.get("court", "")).border = border
            ws.cell(row=row, column=10, value=case.get("status", "")).border = border
            ws.cell(row=row, column=11, value=case.get("created_at", "")).border = border

            # 设置自动换行
            for col in range(1, 12):
                ws.cell(row=row, column=col).alignment = Alignment(wrap_text=True, vertical='center')

        # 调整列宽
        column_widths = [6, 20, 15, 15, 12, 12, 40, 30, 15, 10, 20]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width

        wb.save(output_path)
        return output_path

    def generate_database_element(self, case_data: CaseData, output_path: str) -> str:
        """生成 database_element.xlsx

        字段：公司名、法人姓名、身份证号、手机号、借据、合同编号、贷款本金、期数、
             实际利率、罚息利率、规范罚息利率、借据到期日期、申请日期、欠款总本金、
             贷款本金合计、欠付本金、利息、罚息
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "要素数据库"

        # 样式定义
        header_font = Font(bold=True, size=11, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # 表头
        headers = [
            "公司名", "法人姓名", "身份证号", "手机号",
            "借据", "合同编号", "贷款本金", "期数",
            "实际利率", "罚息利率", "规范罚息利率",
            "借据到期日期", "申请日期", "欠款总本金",
            "贷款本金合计", "欠付本金", "利息", "罚息"
        ]

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border

        # 填充公司基本信息（合并单元格）
        # 每个借款合同一行
        loan_contracts = case_data.loan_contracts.loan_contracts

        if not loan_contracts:
            # 如果没有借款合同，只填充公司信息
            row = 2
            self._fill_row(ws, row, case_data, None, border)
        else:
            for i, loan in enumerate(loan_contracts):
                row = i + 2
                self._fill_row(ws, row, case_data, loan, border)

        # 设置列宽
        column_widths = [25, 10, 20, 15, 25, 25, 12, 8, 10, 10, 12, 15, 15, 12, 12, 12, 12, 12]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width

        wb.save(output_path)
        return output_path

    def _fill_row(self, ws, row: int, case_data: CaseData, loan, border):
        """填充一行数据"""
        # 公司信息
        ws.cell(row=row, column=1, value=case_data.company_info.target_company).border = border
        ws.cell(row=row, column=2, value=case_data.company_info.legal_representative).border = border

        # 被告一身份证号和手机号
        if case_data.defendants:
            ws.cell(row=row, column=3, value=case_data.defendants[0].def_id).border = border
            ws.cell(row=row, column=4, value=case_data.defendants[0].def_tel).border = border
        else:
            ws.cell(row=row, column=3, value="").border = border
            ws.cell(row=row, column=4, value="").border = border

        # 借款合同信息
        if loan:
            ws.cell(row=row, column=5, value=loan.jieju_no).border = border  # 借据号
            ws.cell(row=row, column=6, value=loan.contract_no).border = border  # 合同编号
            ws.cell(row=row, column=7, value=loan.principal).border = border
            ws.cell(row=row, column=8, value=loan.periods).border = border
            ws.cell(row=row, column=9, value=loan.rate).border = border
            ws.cell(row=row, column=10, value=loan.penalty_rate).border = border
            ws.cell(row=row, column=11, value=loan.standard_penalty_rate).border = border
            ws.cell(row=row, column=12, value=loan.due_date).border = border
            ws.cell(row=row, column=13, value=loan.apply_date).border = border
        else:
            for col in range(5, 14):
                ws.cell(row=row, column=col, value="").border = border

        # 债务汇总信息
        ws.cell(row=row, column=14, value=loan.total_principal if loan else "").border = border  # 欠款总本金
        ws.cell(row=row, column=15, value=case_data.debt_info.loan_total).border = border
        ws.cell(row=row, column=16, value=case_data.debt_info.principal).border = border
        ws.cell(row=row, column=17, value=case_data.debt_info.interest).border = border
        ws.cell(row=row, column=18, value=case_data.debt_info.penalty_cutoff).border = border

    def generate_batch_excel(self, cases: List[CaseData], output_path: str) -> str:
        """批量生成多个案件的要素Excel"""
        wb = Workbook()
        ws = wb.active
        ws.title = "要素数据库"

        # 样式定义
        header_font = Font(bold=True, size=11, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # 表头
        headers = [
            "案件ID", "公司名", "法人姓名", "被告一", "被告二",
            "欠付本金", "利息", "罚息", "保全金额",
            "额度合同数", "借款合同数", "贷款本金合计",
            "创建时间", "更新时间"
        ]

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border

        # 数据行
        for row_idx, case in enumerate(cases, 2):
            ws.cell(row=row_idx, column=1, value=case.id).border = border
            ws.cell(row=row_idx, column=2, value=case.company_info.target_company).border = border
            ws.cell(row=row_idx, column=3, value=case.company_info.legal_representative).border = border

            def1 = case.get_defendant_by_index(1)
            def2 = case.get_defendant_by_index(2)
            ws.cell(row=row_idx, column=4, value=def1.def_name).border = border
            ws.cell(row=row_idx, column=5, value=def2.def_name).border = border

            ws.cell(row=row_idx, column=6, value=case.debt_info.principal).border = border
            ws.cell(row=row_idx, column=7, value=case.debt_info.interest).border = border
            ws.cell(row=row_idx, column=8, value=case.debt_info.penalty_cutoff).border = border
            ws.cell(row=row_idx, column=9, value=case.debt_info.guarantee_amount).border = border

            ws.cell(row=row_idx, column=10, value=case.loan_contracts.quota_count).border = border
            ws.cell(row=row_idx, column=11, value=case.loan_contracts.loan_count).border = border
            ws.cell(row=row_idx, column=12, value=case.debt_info.loan_total).border = border

            ws.cell(row=row_idx, column=13, value=case.created_at).border = border
            ws.cell(row=row_idx, column=14, value=case.updated_at).border = border

        # 设置列宽
        column_widths = [10, 25, 10, 10, 10, 12, 12, 12, 12, 10, 10, 12, 20, 20]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width

        wb.save(output_path)
        return output_path
