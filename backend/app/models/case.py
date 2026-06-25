"""
案件完整数据模型
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from .company import CompanyInfo
from .defendant import DefendantInfo
from .loan import LoanContracts
from .debt import DebtInfo


class CaseInfo(BaseModel):
    """案件信息"""
    case_reason: Optional[str] = ""  # 案由（清算责任纠纷/损害公司债权人利益责任纠纷）
    court_name: Optional[str] = ""   # 受理法院名称
    case_number: Optional[str] = ""  # 案号（手动填写）
    judgment_document: Optional[str] = ""  # 判决文书（执行申请书用）
    page_number1: Optional[str] = ""  # 证据目录页码1（放款流水）
    page_number2: Optional[str] = ""  # 证据目录页码2（还款流水）
    page_number3: Optional[str] = ""  # 证据目录页码3（金额计算逻辑）
    cancel_doc: Optional[str] = ""  # 注销文件类型（清算报告/简易注销全体投资人承诺书）


class LawyerLetterInfo(BaseModel):
    """律师函信息"""
    recipient: Optional[str] = ""  # 收件人
    amount: Optional[str] = ""     # 金额
    date: Optional[str] = ""       # 日期
    case_number: Optional[str] = "" # 案号


class ExecutionInfo(BaseModel):
    """执行申请书信息（从民事判决书PDF提取）"""
    judgment_case_number: Optional[str] = ""  # 执行依据判决案号
    judgment_principal: Optional[str] = ""    # 判决本金
    judgment_interest: Optional[str] = ""     # 判决利息
    court_fee: Optional[str] = ""             # 受理费
    preservation_fee: Optional[str] = ""      # 保全费
    notice_fee: Optional[str] = ""            # 公告费


class CaseData(BaseModel):
    """案件完整数据"""
    id: str = ""                           # 案件唯一标识
    company_info: CompanyInfo = CompanyInfo()
    defendants: List[DefendantInfo] = []
    loan_contracts: LoanContracts = LoanContracts()
    debt_info: DebtInfo = DebtInfo()
    case_info: CaseInfo = CaseInfo()
    lawyer_letter_info: LawyerLetterInfo = LawyerLetterInfo()  # 律师函信息
    execution_info: ExecutionInfo = ExecutionInfo()  # 执行申请书信息
    lawer: Optional[str] = ""              # 律师姓名
    created_at: Optional[str] = ""         # 创建时间
    updated_at: Optional[str] = ""         # 更新时间
    source_folder: Optional[str] = ""      # 源文件夹路径

    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4",
                "company_info": {
                    "target_company": "长沙纽威机电科技有限公司",
                    "company_abbr": "纽威机电"
                },
                "defendants": [
                    {"def_name": "陈荣", "def_share": "60%"}
                ],
                "loan_contracts": {
                    "quota_count": 2,
                    "loan_count": 4
                },
                "debt_info": {
                    "principal": "80973.74",
                    "interest": "11194.71"
                },
                "case_info": {
                    "case_reason": "清算责任纠纷",
                    "court_name": "南京市玄武区人民法院"
                },
                "lawer": "赵文"
            }
        }

    def get_defendant_names(self) -> str:
        """获取被告姓名列表，用顿号分隔"""
        names = [d.def_name for d in self.defendants if d.def_name]
        return "、".join(names)

    def get_defendant_by_index(self, index: int) -> DefendantInfo:
        """根据索引获取被告信息，索引从1开始"""
        if 1 <= index <= len(self.defendants):
            return self.defendants[index - 1]
        return DefendantInfo()

    def _build_defendant_lines(self, prefix="被告", format_type="full") -> str:
        """根据实际被告列表动态构建文本块

        Args:
            prefix: 每行的前缀（如"被告"、"被申请人"）
            format_type: 格式类型
                - "full": 完整格式（起诉状、保全申请书使用）
                - "guarantee": 简要格式（保函使用，仅姓名+身份证号）

        Returns:
            用换行符拼接的被告文本块
        """
        lines = []
        for d in self.defendants:
            if format_type == "full":
                line = f"{prefix}：{d.def_name or ''}，{d.def_gender or ''}，"
                line += f"{d.def_nation or ''}族，身份证号码：{d.def_id or ''}，"
                line += f"住址：{d.def_addr or ''}，电话：{d.def_tel or ''}。"
            elif format_type == "guarantee":
                line = f"{d.def_name or ''}，身份证号码：{d.def_id or ''}"
            lines.append(line)
        return "\n".join(lines)

    def to_template_vars(self) -> dict:
        """转换为模板变量字典，用于文书生成"""
        def1 = self.get_defendant_by_index(1)
        def2 = self.get_defendant_by_index(2)

        # 获取额度合同日期
        quota_dates = [qc.contract_date for qc in self.loan_contracts.quota_contracts if qc.contract_date]
        loan_dates = [lc.contract_date for lc in self.loan_contracts.loan_contracts if lc.contract_date]

        # 计算借款合同汇总（按规范罚息利率分组）
        loan_summary = {}
        for loan in self.loan_contracts.loan_contracts:
            key = loan.standard_penalty_rate or "24.00%"
            if key not in loan_summary:
                loan_summary[key] = {
                    "principal": 0,
                    "rate": loan.standard_penalty_rate or "24.00%",
                    "penalty_rate": loan.penalty_rate,
                    "standard_penalty_rate": loan.standard_penalty_rate,
                    "count": 0
                }
            loan_summary[key]["principal"] += float(loan.total_principal or loan.principal or 0)
            loan_summary[key]["count"] += 1

        # 转换为列表并格式化
        loan_summary_list = []
        for i, (key, data) in enumerate(loan_summary.items(), 1):
            loan_summary_list.append({
                "index": i,
                "principal": f"{data['principal']:.2f}",
                "rate": data["rate"],
                "penalty_rate": data["penalty_rate"],
                "standard_penalty_rate": data["standard_penalty_rate"],
                "count": data["count"]
            })

        # 计算保全金额
        guarantee = self.debt_info.calculate_guarantee_amount()
        if not self.debt_info.guarantee_amount:
            self.debt_info.guarantee_amount = guarantee

        # 计算取整保全金额
        guarantee_rounded = self.debt_info.calculate_guarantee_amount_rounded()
        if not self.debt_info.guarantee_amount_rounded:
            self.debt_info.guarantee_amount_rounded = guarantee_rounded

        # 推荐法院
        court = self.case_info.court_name
        if not court and def1.def_addr:
            from ..core.agent import LegalAgent
            agent = LegalAgent()
            court = agent.recommend_court(def1.def_addr)

        # 当前日期
        today = datetime.now()
        date_str = today.strftime("%Y年%m月%d日")

        # 格式化注册资本
        capital = CompanyInfo.format_capital(self.company_info.company_capital)

        # 构建额度合同日期文本（动态数量）
        quota_dates_text = "、".join(quota_dates) if quota_dates else "【额度合同日期】"

        # 构建借款合同签订日期文本（动态数量）
        loan_dates_text = "、".join([d for d in loan_dates if d]) if loan_dates else "【借款合同日期】"

        # 构建借款合同汇总罚息条款文本（动态数量，按实际分组）
        penalty_text_parts = []
        for item in loan_summary_list:
            penalty_text_parts.append(f"以{item['principal']}元为基数，按年利率{item['standard_penalty_rate']}的标准")
        penalty_text = "；".join(penalty_text_parts) if penalty_text_parts else "以【本金】元为基数，按年利率24.00%的标准"

        # 构建借款合同证明文本（动态数量，每份合同单独列出）
        loan_contract_proof_parts = []
        for loan in self.loan_contracts.loan_contracts:
            if loan.contract_date and loan.principal and loan.rate:
                loan_contract_proof_parts.append(
                    f"{loan.contract_date}签订借款本金为{loan.principal}元，年利率为{loan.rate}的《借款合同》"
                )
        loan_contract_proof = "；".join(loan_contract_proof_parts) if loan_contract_proof_parts else "【借款合同证明】"

        # 构建放款存证证明文本（动态数量）
        loan_flow_proof_parts = []
        # 收集所有放款日期和金额
        loan_flow_dates = []
        loan_flow_total = 0
        for loan in self.loan_contracts.loan_contracts:
            if loan.contract_date:
                loan_flow_dates.append(loan.contract_date)
            if loan.principal:
                loan_flow_total += float(loan.principal or 0)
        loan_flow_dates_text = "、".join(loan_flow_dates) if loan_flow_dates else "【放款日期】"
        loan_flow_proof = f"原告于{loan_flow_dates_text}向{self.company_info.target_company or '【公司名】'}账户支付{loan_flow_total:.2f}元借款，放款成功。"

        # 动态生成额度合同日期变量（loan_quota_date1, loan_quota_date2, ...）
        quota_date_vars = {}
        for i, qd in enumerate(quota_dates, 1):
            quota_date_vars[f"loan_quota_date{i}"] = qd

        # 动态生成借款合同签订日期变量（loan_contract_date1, loan_contract_date2, ...）
        loan_date_vars = {}
        for i, ld in enumerate(loan_dates, 1):
            loan_date_vars[f"loan_contract_date{i}"] = ld

        # 动态生成罚息利率条款变量（principal1, principal_rate1, penalty_cutoff1, ...）
        penalty_vars = {}
        for i, item in enumerate(loan_summary_list, 1):
            penalty_vars[f"principal{i}"] = item["principal"]
            penalty_vars[f"principal_rate{i}"] = item["standard_penalty_rate"]
            penalty_vars[f"penalty_cutoff{i}"] = item["standard_penalty_rate"]

        return {
            # 被告一信息
            "def1_name": def1.def_name or "【被告一姓名】",
            "def1_gender": def1.def_gender or "【性别】",
            "def1_nation": def1.def_nation or "【民族】",
            "def1_id": def1.def_id or "【身份证号】",
            "def1_addr": def1.def_addr or "【住址】",
            "def1_tel": def1.def_tel or "【电话】",
            "def1_share": def1.def_share or "【持股比例】",
            # 被告二信息
            "def2_name": def2.def_name or "【被告二姓名】",
            "def2_gender": def2.def_gender or "【性别】",
            "def2_nation": def2.def_nation or "【民族】",
            "def2_id": def2.def_id or "【身份证号】",
            "def2_addr": def2.def_addr or "【住址】",
            "def2_tel": def2.def_tel or "【电话】",
            "def2_share": def2.def_share or "【持股比例】",
            # 动态被告文本（根据实际被告数量动态生成，替代硬编码的 def1_/def2_ 段落）
            "defendants_text": self._build_defendant_lines("被告", "full"),
            "respondents_text": self._build_defendant_lines("被申请人", "full"),
            "guarantee_defendants_text": self._build_defendant_lines(format_type="guarantee"),
            # 公司信息
            "target_company": self.company_info.target_company or "【公司名】",
            "company_abbr": self.company_info.company_abbr or "【简称】",
            "company_capital": capital or "【注册资本】",
            "company_establish": self.company_info.company_establish or "【成立日期】",
            "company_cancel_apply": self.company_info.company_cancel_apply or "【核准日期】",
            "company_cancel_date": self.company_info.company_cancel_date or "【注销日期】",
            "company_cancel_approve": self.company_info.company_cancel_apply or "【核准日期】",
            "cancel_doc": self.case_info.cancel_doc or "",
            "company_addr": self.company_info.company_addr or "【住所】",
            "company_reg": self.company_info.company_reg or "【登记机关】",
            "capital_status": self.company_info.capital_status or "【出资状态】",
            "subscribe_date": self.company_info.subscribe_date or "【认缴日期】",
            "Legal_representative": self.company_info.legal_representative or "【法定代表人】",
            # 债务信息
            "principal": self.debt_info.principal or "【本金】",
            "interest": self.debt_info.interest or "【利息】",
            "penalty_cutoff": self.debt_info.penalty_cutoff or "【罚息】",
            "loan_total": self.debt_info.loan_total or "【贷款本金】",
            "end_date": self.debt_info.end_date or "【截止日期】",
            "start_date": self.debt_info.start_date or "【起算日期】",
            "guarantee_amount": self.debt_info.guarantee_amount or guarantee or "【保全金额】",
            " guarantee_amount": self.debt_info.guarantee_amount or guarantee or "【保全金额】",  # 带空格版本
            "guarantee_amount_rounded": self.debt_info.guarantee_amount_rounded or guarantee_rounded or "【取整保全金额】",
            " guarantee_amount_rounded": self.debt_info.guarantee_amount_rounded or guarantee_rounded or "【取整保全金额】",
            "round-off_guarantee_amount": self.debt_info.guarantee_amount_rounded or guarantee_rounded or "【取整保全金额】",
            " round-off_guarantee_amount": self.debt_info.guarantee_amount_rounded or guarantee_rounded or "【取整保全金额】",
            # 合同信息 - 固定变量（兼容旧模板）
            "loan_quota_num": str(self.loan_contracts.quota_count) or "0",
            "loan_contract_num": str(self.loan_contracts.loan_count) or "0",
            # 动态合同变量（新模板使用）
            "quota_dates_text": quota_dates_text,
            "loan_dates_text": loan_dates_text,
            "loan_quota_date": quota_dates_text,
            "loan_contract_date": loan_dates_text,
            "penalty_text": penalty_text,
            "loan_contract_proof": loan_contract_proof,
            "loan_flow_proof": loan_flow_proof,
            "loan_summary": loan_summary_list,
            "loan_summary_count": len(loan_summary_list),
            # 动态变量（按实际数量）
            **quota_date_vars,
            **loan_date_vars,
            **penalty_vars,
            # 案件信息
            "case_reason": self.case_info.case_reason or "【案由】",
            "court_name": court or "【受理法院】",
            "court": court or "【受理法院】",  # 别名
            "def": self.get_defendant_names() or "【被告】",
            "lawer": self.lawer or "赵文",
            # 新增变量
            "date": date_str,
            "日期": date_str,
            "case number": self.case_info.case_number or "【案号】",
            "案号": self.case_info.case_number or "【案号】",
            "judgment document": self.case_info.judgment_document or "【判决文书】",
            "judgment_case_number": self.execution_info.judgment_case_number or "【执行依据判决案号】",
            "judgment_principal": self.execution_info.judgment_principal or "【判决本金】",
            "judgment_interest": self.execution_info.judgment_interest or "【判决利息】",
            "court_fee": self.execution_info.court_fee or "【受理费】",
            "preservation_fee": self.execution_info.preservation_fee or "【保全费】",
            "notice_fee": self.execution_info.notice_fee or "【公告费】",
            "page number1": str(self.case_info.page_number1 or ""),
            "page number2": str(self.case_info.page_number2 or ""),
            "page number3": str(self.case_info.page_number3 or ""),
            "收件人": self.lawyer_letter_info.recipient or "【收件人】",
            "金额": self.lawyer_letter_info.amount or self.debt_info.principal or "【金额】",
        }
