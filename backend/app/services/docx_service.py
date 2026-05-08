"""
Word 文档生成服务 - 重构版
支持模板变量替换
"""
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from typing import Dict
import os
import copy


class DocxService:
    """Word 文档生成服务"""

    def generate_complaint(self, case: dict, content: str, output_path: str):
        """生成民事起诉状"""
        doc = Document()

        # 标题
        title = doc.add_paragraph("民事起诉状")
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title.runs[0]
        title_run.font.size = Pt(22)
        title_run.font.bold = True

        doc.add_paragraph()

        # 原告信息
        p = doc.add_paragraph()
        p.add_run("原告：").bold = True
        p.add_run(case.get("plaintiff", "待填写"))

        # 被告信息
        p = doc.add_paragraph()
        p.add_run("被告：").bold = True
        p.add_run(case.get("defendant", "待填写"))

        doc.add_paragraph()

        # 诉讼请求
        p = doc.add_paragraph()
        p.add_run("诉讼请求：").bold = True
        doc.add_paragraph("1. 判令被告偿还债务本金及利息")
        doc.add_paragraph("2. 判令被告承担本案诉讼费用")

        doc.add_paragraph()

        # 事实与理由
        p = doc.add_paragraph()
        p.add_run("事实与理由：").bold = True

        facts = case.get("facts", content)
        p = doc.add_paragraph(facts if facts else "待填写")

        doc.add_paragraph()
        doc.add_paragraph()

        # 此致
        p = doc.add_paragraph()
        p.add_run("此致").bold = True

        court = case.get("court", "XX人民法院")
        doc.add_paragraph(court)

        doc.add_paragraph()
        doc.add_paragraph()

        # 签名
        p = doc.add_paragraph()
        p.add_run("原告：______________")
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        # 日期
        from datetime import datetime
        p = doc.add_paragraph()
        p.add_run(datetime.now().strftime("%Y年%m月%d日"))
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        doc.save(output_path)
        return output_path

    def generate_evidence_list(self, case, output_path: str):
        """生成证据目录"""
        doc = Document()

        # 标题
        title = doc.add_paragraph("证据目录")
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title.runs[0]
        title_run.font.size = Pt(18)
        title_run.font.bold = True

        doc.add_paragraph()

        # 案件信息
        p = doc.add_paragraph()
        p.add_run("案号：").bold = True
        p.add_run("（待分配）")

        # 获取原告和被告信息
        if hasattr(case, 'company_info'):
            plaintiff = case.company_info.target_company or ""
        else:
            plaintiff = case.get("plaintiff", "")

        if hasattr(case, 'defendants'):
            defendant = "、".join([d.def_name for d in case.defendants if d.def_name])
        else:
            defendant = case.get("defendant", "")

        p = doc.add_paragraph()
        p.add_run("原告：").bold = True
        p.add_run(plaintiff)

        p = doc.add_paragraph()
        p.add_run("被告：").bold = True
        p.add_run(defendant)

        doc.add_paragraph()

        # 证据表格
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Table Grid'

        # 表头
        header_cells = table.rows[0].cells
        headers = ["序号", "证据名称", "证明目的", "页码"]
        for i, header in enumerate(headers):
            header_cells[i].text = header
            for paragraph in header_cells[i].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True

        # 证据列表
        if hasattr(case, 'evidence'):
            evidence_list = case.evidence or ["证据1", "证据2", "证据3"]
        else:
            evidence_list = case.get("evidence", ["证据1", "证据2", "证据3"])

        for i, evidence in enumerate(evidence_list, 1):
            row = table.add_row().cells
            row[0].text = str(i)
            row[1].text = evidence
            row[2].text = ""
            row[3].text = ""

        doc.save(output_path)
        return output_path

    def generate_application(self, case, content: str, output_path: str):
        """生成申请书"""
        doc = Document()

        # 标题
        title = doc.add_paragraph("申请书")
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title.runs[0]
        title_run.font.size = Pt(18)
        title_run.font.bold = True

        doc.add_paragraph()

        # 申请人信息
        p = doc.add_paragraph()
        p.add_run("申请人：").bold = True
        if hasattr(case, 'company_info'):
            p.add_run(case.company_info.target_company or "")
        else:
            p.add_run(case.get("plaintiff", ""))

        p = doc.add_paragraph()
        p.add_run("被申请人：").bold = True
        if hasattr(case, 'defendants'):
            p.add_run("、".join([d.def_name for d in case.defendants if d.def_name]))
        else:
            p.add_run(case.get("defendant", ""))

        doc.add_paragraph()

        # 申请事项
        p = doc.add_paragraph()
        p.add_run("申请事项：").bold = True
        doc.add_paragraph("请求法院依法对本案进行审理")

        doc.add_paragraph()

        # 事实与理由
        p = doc.add_paragraph()
        p.add_run("事实与理由：").bold = True

        if hasattr(case, 'debt_info'):
            facts = f"申请人申请对被申请人进行财产保全，保全金额为{case.debt_info.guarantee_amount or ''}元。"
        else:
            facts = case.get("facts", content)

        p = doc.add_paragraph(facts if facts else "待填写")

        doc.add_paragraph()
        doc.add_paragraph()

        # 此致
        p = doc.add_paragraph()
        p.add_run("此致").bold = True
        if hasattr(case, 'case_info'):
            doc.add_paragraph(case.case_info.court_name or "XX人民法院")
        else:
            doc.add_paragraph(case.get("court", "XX人民法院"))

        doc.add_paragraph()

        # 签名
        p = doc.add_paragraph()
        p.add_run("申请人：______________")
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        from datetime import datetime
        p = doc.add_paragraph()
        p.add_run(datetime.now().strftime("%Y年%m月%d日"))
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        doc.save(output_path)
        return output_path

    def generate_from_template(self, template_path: str, variables: Dict, output_path: str):
        """从模板生成文档，替换变量

        Args:
            template_path: 模板文件路径
            variables: 变量字典，key为变量名（不含花括号），value为替换值
            output_path: 输出文件路径
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板文件不存在: {template_path}")

        doc = Document(template_path)

        # 替换段落中的变量
        for para in doc.paragraphs:
            self._replace_paragraph_variables(para, variables)

        # 替换表格中的变量
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        self._replace_paragraph_variables(para, variables)

        doc.save(output_path)
        return output_path

    def _replace_paragraph_variables(self, para, variables: Dict):
        """替换单个段落中的变量"""
        full_text = para.text

        # 检查是否包含变量
        if "{" not in full_text or "}" not in full_text:
            return

        # 构建新文本
        new_text = full_text
        for key, value in variables.items():
            # 标准格式: {variable}
            placeholder = "{" + key + "}"
            # 带空格格式: { variable } (模板中可能存在的格式问题)
            placeholder_with_space = "{ " + key + "}"

            # 替换值
            replace_value = str(value) if value else f"【{key}】"

            # 替换两种格式
            if placeholder in new_text:
                new_text = new_text.replace(placeholder, replace_value)
            if placeholder_with_space in new_text:
                new_text = new_text.replace(placeholder_with_space, replace_value)

        # 如果文本有变化，替换段落内容
        if new_text != full_text:
            # 保存原格式
            if para.runs:
                # 获取第一个run的格式作为模板
                first_run = para.runs[0]
                font_name = first_run.font.name
                font_size = first_run.font.size
                font_bold = first_run.font.bold

                # 清空段落
                para.clear()

                # 添加新文本，保留格式
                run = para.add_run(new_text)
                if font_name:
                    run.font.name = font_name
                if font_size:
                    run.font.size = font_size
                if font_bold is not None:
                    run.font.bold = font_bold
            else:
                # 没有run，直接替换文本
                para.text = new_text

    def batch_generate_from_template(self, template_path: str, cases: list, output_dir: str) -> list:
        """批量从模板生成文档

        Args:
            template_path: 模板文件路径
            cases: 案件列表（CaseData对象）
            output_dir: 输出目录

        Returns:
            生成的文件路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        output_files = []

        for case in cases:
            # 获取模板变量
            variables = case.to_template_vars()

            # 生成文件名
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"{case.company_info.target_company or case.id}_{timestamp}.docx"
            output_path = os.path.join(output_dir, output_filename)

            # 生成文档
            self.generate_from_template(template_path, variables, output_path)
            output_files.append(output_path)

        return output_files
