"""
文件抽取服务 - 从PDF和Excel文件中提取结构化数据
"""
import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from ..services.pdf_service import PDFService
from ..models.case import CaseData, CompanyInfo, DefendantInfo, LoanContracts, DebtInfo, CaseInfo
from ..models.loan import QuotaContract, LoanContract


class ExtractorService:
    """文件抽取服务"""

    # 需要提取的关键文件类型（白名单）
    KEY_FILE_PATTERNS = {
        "public_report": ["公示系统", "企业信用信息公示"],
        "id_card_front": ["身份证正面照片", "身份证正面"],
        "id_card_back": ["身份证反面照片", "身份证反面"],
        "quota_contract": ["额度合同"],
        "loan_contract": ["借款合同"],
        "loan_flow": ["放款流水", "放款存证"],
        "repay_flow": ["还款流水"],
        "guarantee_contract": ["担保合同"],
        "calc_logic": ["金额计算逻辑"]
    }

    # 干扰文件关键词（黑名单）- 这些文件不需要处理
    IGNORE_PATTERNS = [
        "个人信息使用授权书", "个人信息处理授权书", "个人征信授权书", "个人授权委托书",
        "企业信息使用授权书", "企业信息处理授权书", "企业征信授权书", "企业授权委托书", "企业授权协议书",
        "授信申请声明书", "仲裁申请书", "送达地址确认书", "送达地址线索书",
        "法定代表人身份证明书", "营业执照", "借款合同编号",
        "提前到期后还款计划表", "证据目录", "合同类映射表",
        ".zip", "保证合同", "原告送达",
        "~$"  # Excel临时文件
    ]

    def __init__(self):
        self.pdf_service = PDFService()

    def is_ignored_file(self, filename: str) -> bool:
        """检查是否是需要忽略的干扰文件"""
        for pattern in self.IGNORE_PATTERNS:
            if pattern in filename:
                return True
        return False

    def classify_file(self, filename: str) -> str:
        """根据文件名分类文件类型"""
        # 先检查是否需要忽略
        if self.is_ignored_file(filename):
            return "ignored"

        for file_type, patterns in self.KEY_FILE_PATTERNS.items():
            for pattern in patterns:
                if pattern in filename:
                    return file_type

        return "other"

    def extract_contract_info_from_filename(self, filename: str) -> Dict:
        """从合同文件名提取合同编号和日期

        命名格式示例：
        - "1.1.0额度合同_EDXS0240708001677390_2024年07月08日10时36分46秒.pdf"
        - "1.1.2借款合同_JH20240708XS0M00012078_2024年07月08日10时36分49秒.pdf"
        """
        result = {
            "contract_no": "",
            "contract_date": "",
            "serial_no": ""  # 序号如 1.1.0, 1.1.2
        }

        # 提取序号
        serial_match = re.match(r'^[\d\.]+', filename)
        if serial_match:
            result["serial_no"] = serial_match.group().rstrip('.')

        # 提取合同编号 - 格式：大写字母+数字组合
        # 匹配模式如：EDXS0240708001677390, JH20240708XS0M00012078
        contract_match = re.search(r'_([A-Z]{2,}\d[A-Z0-9]+)_', filename)
        if contract_match:
            result["contract_no"] = contract_match.group(1)

        # 提取日期 - 格式：2024年07月08日
        date_match = re.search(r'(\d{4}年\d{2}月\d{2}日)', filename)
        if date_match:
            result["contract_date"] = date_match.group(1)

        return result

    def extract_from_excel(self, excel_path: str) -> Dict:
        """从金额计算逻辑Excel提取数据

        Excel结构：
        - 第1行：企业基本信息和债务汇总
          - 位置1: 企业名称, 位置3: 证件号码, 位置5: 法人姓名
          - 位置7: 身份证号, 位置9: 手机号, 位置11: 本金
          - 位置13: 利息, 位置15: 罚息
        - 第5行起：借据汇总（借据、贷款本金、期数、实际利率、罚息利率、借据到期日期、申请日期）
        - 详细表格：借据、合同编号、...、欠款总本金
        """
        try:
            import pandas as pd
            print(f"[Excel解析] 开始解析: {excel_path}")
            df = pd.read_excel(excel_path, header=None)

            result = {
                "company_info": {},
                "debt_info": {},
                "loan_contracts": [],
                "repayment_details": []
            }

            # 第一部分：企业基本信息（第1行）
            row0 = df.iloc[0]

            def safe_get(idx, default=""):
                if idx < len(row0) and pd.notna(row0[idx]):
                    return str(row0[idx]).strip()
                return default

            result["company_info"]["target_company"] = safe_get(1)  # 企业名称
            result["company_info"]["company_id"] = safe_get(3)       # 证件号码
            result["company_info"]["legal_representative"] = safe_get(5)  # 法人姓名
            result["company_info"]["legal_rep_id"] = safe_get(7)     # 身份证号
            result["company_info"]["legal_rep_tel"] = safe_get(9)    # 手机号

            result["debt_info"]["principal"] = safe_get(11)   # 欠付本金
            result["debt_info"]["interest"] = safe_get(13)    # 利息
            result["debt_info"]["penalty_cutoff"] = safe_get(15)  # 罚息

            print(f"[Excel提取] 企业名称: {result['company_info']['target_company']}")
            print(f"[Excel提取] 法人: {result['company_info']['legal_representative']}")
            print(f"[Excel提取] 本金: {result['debt_info']['principal']}, 利息: {result['debt_info']['interest']}, 罚息: {result['debt_info']['penalty_cutoff']}")

            # 第二部分：借据汇总（第5行起，索引4）
            loan_contracts = []
            loan_sum = 0
            for idx in range(4, len(df)):
                row = df.iloc[idx]
                jieju = row[0]

                if pd.isna(jieju) or str(jieju).strip() == '' or '合计' in str(jieju):
                    continue

                jieju_str = str(jieju)
                if not (jieju_str.startswith('JH') or jieju_str.startswith('JQ')):
                    break

                loan = {
                    "jieju_no": jieju_str,  # 借据号
                    "principal": str(row[1]) if pd.notna(row[1]) else "",    # 贷款本金
                    "periods": str(row[2]) if pd.notna(row[2]) else "",      # 期数
                    "rate": str(row[3]) if pd.notna(row[3]) else "",         # 实际利率
                    "penalty_rate": str(row[4]) if pd.notna(row[4]) else "", # 罚息利率
                    "due_date": str(row[6]) if pd.notna(row[6]) else "",     # 借据到期日期
                    "apply_date": str(row[7]) if pd.notna(row[7]) else "",   # 申请日期
                    "contract_no": "",  # 合同编号（从详细表格补充）
                    "total_principal": ""  # 欠款总本金（从详细表格补充）
                }

                # 计算规范罚息利率
                if loan["rate"]:
                    loan["standard_penalty_rate"] = self.calculate_standard_penalty_rate(loan["rate"], loan["penalty_rate"])

                loan_contracts.append(loan)

                # 累计贷款本金
                try:
                    loan_sum += float(row[1])
                except (ValueError, TypeError):
                    pass

            result["loan_contracts"] = loan_contracts
            result["debt_info"]["loan_total"] = f"{loan_sum:.2f}"

            # 提取截止日期（从第一个借据的申请日期，H列=索引7）
            if loan_contracts:
                first_apply_date = loan_contracts[0].get("apply_date", "")
                end_date, start_date = self._format_end_dates(first_apply_date)
                result["debt_info"]["end_date"] = end_date
                result["debt_info"]["start_date"] = start_date
                result["debt_info"]["cutoff_date"] = end_date  # 兼容旧字段
                print(f"[Excel提取] 截止日期: {end_date}, 起算日期: {start_date}")

            # 第三部分：提取合同编号和欠款总本金（从详细表格）
            detail_start = None
            for idx in range(len(df)):
                cell_val = str(df.iloc[idx, 0]) if pd.notna(df.iloc[idx, 0]) else ''
                cell_val1 = str(df.iloc[idx, 1]) if pd.notna(df.iloc[idx, 1]) else ''
                if '借据' in cell_val and '合同编号' in cell_val1:
                    detail_start = idx + 1
                    break

            if detail_start:
                contract_info = {}
                # 收集借据和合同编号
                for idx in range(detail_start, len(df)):
                    row = df.iloc[idx]
                    jieju = row[0]
                    contract_no = row[1]

                    if pd.isna(jieju) or str(jieju).strip() == '':
                        continue

                    jieju_str = str(jieju)
                    if not (jieju_str.startswith('JH') or jieju_str.startswith('JQ')):
                        continue

                    if jieju_str not in contract_info:
                        contract_info[jieju_str] = {
                            "contract_no": str(contract_no) if pd.notna(contract_no) else "",
                            "total_principal": None
                        }

                # 查找C列包含'汇总'的行，获取欠款总本金
                for idx in range(detail_start, len(df)):
                    row = df.iloc[idx]
                    c_val = str(row[2]) if pd.notna(row[2]) else ''

                    if '汇总' in c_val:
                        jieju = row[0]
                        if pd.notna(jieju):
                            jieju_str = str(jieju)
                            if jieju_str in contract_info:
                                p_val = row[15]  # P列是欠款总本金
                                if pd.notna(p_val):
                                    contract_info[jieju_str]["total_principal"] = str(p_val)

                # 补充到loan_contracts
                for loan in result["loan_contracts"]:
                    jieju = loan["jieju_no"]
                    if jieju in contract_info:
                        info = contract_info[jieju]
                        if info["contract_no"]:
                            loan["contract_no"] = info["contract_no"]
                        if info["total_principal"]:
                            loan["total_principal"] = info["total_principal"]

            # 计算保全金额
            try:
                principal = float(result["debt_info"].get("principal", 0) or 0)
                interest = float(result["debt_info"].get("interest", 0) or 0)
                penalty = float(result["debt_info"].get("penalty_cutoff", 0) or 0)
                result["debt_info"]["guarantee_amount"] = f"{principal + interest + penalty:.2f}"
            except ValueError:
                result["debt_info"]["guarantee_amount"] = ""

            print(f"[Excel解析] 解析成功，借据数: {len(loan_contracts)}")
            return result

        except PermissionError as e:
            print(f"[Excel解析] 文件被占用，跳过: {excel_path}")
            return {}
        except Exception as e:
            print(f"[Excel解析] 解析错误: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def calculate_standard_penalty_rate(self, rate: str, penalty_rate: str) -> str:
        """计算规范罚息利率

        规则：
        1. 规范罚息利率 = 实际利率 × 1.5
        2. 最高不超过24%
        """
        try:
            # 提取利率数值
            rate_value = float(rate.replace("%", "")) / 100
            standard = rate_value * 1.5

            # 最高24%
            if standard > 0.24:
                standard = 0.24

            return f"{standard * 100:.2f}%"
        except (ValueError, AttributeError):
            return "24.00%"  # 默认最高值

    def _format_end_dates(self, apply_date_str: str):
        """将申请日期转换为end_date和start_date（中国日期格式）

        Args:
            apply_date_str: Excel中的申请日期，可能是"2026-03-03"、"2026/03/03"或pandas Timestamp格式

        Returns:
            (end_date, start_date): end_date格式如"2026年3月3日"，start_date为end_date+1天
        """
        if not apply_date_str:
            return "", ""

        try:
            import pandas as pd

            # 尝试多种格式解析
            date_obj = None
            clean_str = str(apply_date_str).strip()

            # 处理pandas Timestamp格式
            if isinstance(apply_date_str, pd.Timestamp):
                date_obj = apply_date_str.to_pydatetime()
            else:
                # 尝试常见日期格式
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"]:
                    try:
                        date_obj = datetime.strptime(clean_str, fmt)
                        break
                    except ValueError:
                        continue

            if date_obj is None:
                print(f"[日期转换] 无法解析日期: {apply_date_str}")
                return "", ""

            # 格式化为中国日期：2026年3月3日
            end_date = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"

            # start_date = end_date + 1天
            next_day = date_obj + timedelta(days=1)
            start_date = f"{next_day.year}年{next_day.month}月{next_day.day}日"

            return end_date, start_date

        except Exception as e:
            print(f"[日期转换] 错误: {e}")
            return "", ""

    def process_company_folder(self, folder_path: str, agent=None) -> CaseData:
        """处理公司文件夹，提取所有数据

        Args:
            folder_path: 公司文件夹路径
            agent: AI Agent实例，用于解析PDF文本

        Returns:
            CaseData: 案件完整数据
        """
        case_data = CaseData()
        case_data.source_folder = folder_path

        # 从文件夹名提取公司ID
        folder_name = os.path.basename(folder_path)
        if "_" in folder_name:
            case_data.id = folder_name.split("_")[0]

        # 收集所有文件
        files = {}
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                file_type = self.classify_file(filename)
                if file_type not in files:
                    files[file_type] = []
                files[file_type].append({
                    "filename": filename,
                    "path": file_path
                })

        # 1. 处理金额计算Excel
        excel_data = {}
        if "calc_logic" in files:
            # 只处理xlsx文件，过滤临时文件
            excel_files = [f for f in files["calc_logic"]
                          if f["filename"].endswith(".xlsx") and not f["filename"].startswith("~$")]
            print(f"[文件处理] 找到 {len(excel_files)} 个Excel文件")
            if excel_files:
                excel_file = excel_files[0]
                print(f"[文件处理] 处理Excel: {excel_file['filename']}")
                excel_data = self.extract_from_excel(excel_file["path"]) or {}

            # 填充公司信息
            if excel_data.get("company_info"):
                case_data.company_info.target_company = excel_data["company_info"].get("target_company", "")
                case_data.company_info.company_id = excel_data["company_info"].get("company_id", "")
                case_data.company_info.legal_representative = excel_data["company_info"].get("legal_representative", "")

                # 法定代表人作为被告一
                if case_data.company_info.legal_representative:
                    def1 = DefendantInfo(
                        def_name=excel_data["company_info"].get("legal_representative", ""),
                        def_id=excel_data["company_info"].get("legal_rep_id", ""),
                        def_tel=excel_data["company_info"].get("legal_rep_tel", ""),
                        is_legal_rep=True
                    )
                    case_data.defendants.append(def1)
                    print(f"[数据填充] 添加被告: {def1.def_name}")

            # 填充债务信息
            if excel_data.get("debt_info"):
                case_data.debt_info.loan_total = excel_data["debt_info"].get("loan_total", "")
                case_data.debt_info.principal = excel_data["debt_info"].get("principal", "")
                case_data.debt_info.interest = excel_data["debt_info"].get("interest", "")
                case_data.debt_info.penalty_cutoff = excel_data["debt_info"].get("penalty_cutoff", "")
                case_data.debt_info.cutoff_date = excel_data["debt_info"].get("cutoff_date", "")
                case_data.debt_info.end_date = excel_data["debt_info"].get("end_date", "")
                case_data.debt_info.start_date = excel_data["debt_info"].get("start_date", "")
                case_data.debt_info.guarantee_amount = excel_data["debt_info"].get("guarantee_amount", "")
                print(f"[数据填充] 债务信息: 贷款本金合计={case_data.debt_info.loan_total}, 欠付本金={case_data.debt_info.principal}, 利息={case_data.debt_info.interest}, 截止日期={case_data.debt_info.end_date}")

        # 2. 处理额度合同PDF
        if "quota_contract" in files:
            for file_info in files["quota_contract"]:
                contract_info = self.extract_contract_info_from_filename(file_info["filename"])
                quota = QuotaContract(
                    contract_no=contract_info["contract_no"],
                    contract_date=contract_info["contract_date"]
                )
                case_data.loan_contracts.quota_contracts.append(quota)

        case_data.loan_contracts.quota_count = len(case_data.loan_contracts.quota_contracts)

        # 3. 处理借款合同PDF - 优先从Excel提取数据
        # 先从Excel获取借款合同数据（更完整）
        if excel_data.get("loan_contracts"):
            for loan_data in excel_data["loan_contracts"]:
                loan = LoanContract(
                    jieju_no=loan_data.get("jieju_no", ""),
                    contract_no=loan_data.get("contract_no", ""),
                    principal=loan_data.get("principal", ""),
                    rate=loan_data.get("rate", ""),
                    penalty_rate=loan_data.get("penalty_rate", ""),
                    standard_penalty_rate=loan_data.get("standard_penalty_rate", ""),
                    periods=loan_data.get("periods", ""),
                    due_date=loan_data.get("due_date", ""),
                    apply_date=loan_data.get("apply_date", ""),
                    total_principal=loan_data.get("total_principal", "")
                )
                case_data.loan_contracts.loan_contracts.append(loan)

        # 如果Excel没有数据，再从PDF文件名提取
        if not case_data.loan_contracts.loan_contracts and "loan_contract" in files:
            for file_info in files["loan_contract"]:
                contract_info = self.extract_contract_info_from_filename(file_info["filename"])
                loan = LoanContract(
                    jieju_no=contract_info["contract_no"],  # PDF文件名中的合同编号可能是借据号
                    contract_no=contract_info["contract_no"],
                    contract_date=contract_info["contract_date"]
                )
                case_data.loan_contracts.loan_contracts.append(loan)

        # 补充合同日期（从PDF文件名匹配借据号）
        # 匹配规则：忽略借据号末尾的WB后缀
        def normalize_jieju(jieju_no):
            """标准化借据号，去除末尾WB后缀用于匹配"""
            if jieju_no and jieju_no.endswith("WB"):
                return jieju_no[:-2]
            return jieju_no

        if "loan_contract" in files:
            # 构建PDF文件名中的借据号到日期的映射
            pdf_date_map = {}
            for file_info in files["loan_contract"]:
                contract_info = self.extract_contract_info_from_filename(file_info["filename"])
                file_contract_no = contract_info["contract_no"]
                contract_date = contract_info["contract_date"]
                if file_contract_no and contract_date:
                    # 标准化借据号（去除WB）
                    normalized_no = normalize_jieju(file_contract_no)
                    pdf_date_map[normalized_no] = contract_date
                    print(f"[日期匹配] PDF借据号: {file_contract_no} -> 标准化: {normalized_no}, 日期: {contract_date}")

            # 匹配并填充日期
            for loan in case_data.loan_contracts.loan_contracts:
                if not loan.contract_date:
                    # 尝试用借据号匹配
                    if loan.jieju_no:
                        normalized_jieju = normalize_jieju(loan.jieju_no)
                        if normalized_jieju in pdf_date_map:
                            loan.contract_date = pdf_date_map[normalized_jieju]
                            print(f"[日期匹配] 匹配成功: 借据{loan.jieju_no} -> 标准化{normalized_jieju} -> 日期{loan.contract_date}")
                            continue

                    # 尝试用合同编号匹配
                    if loan.contract_no:
                        normalized_contract = normalize_jieju(loan.contract_no)
                        if normalized_contract in pdf_date_map:
                            loan.contract_date = pdf_date_map[normalized_contract]
                            print(f"[日期匹配] 匹配成功: 合同{loan.contract_no} -> 标准化{normalized_contract} -> 日期{loan.contract_date}")

        print(f"[数据填充] 借款合同数: {len(case_data.loan_contracts.loan_contracts)}")

        case_data.loan_contracts.loan_count = len(case_data.loan_contracts.loan_contracts)

        # 4. 处理公示系统PDF（直接使用规则解析，快速可靠）
        if "public_report" in files and agent:
            public_file = files["public_report"][0]
            pdf_text = self.pdf_service.extract_text(public_file["path"])
            if pdf_text:
                print(f"[公示系统] 正在解析: {public_file['filename']}")
                # 直接使用规则解析（快速）
                company_info = agent._parse_public_report_rules(pdf_text)

                if company_info:
                    case_data.company_info.target_company = company_info.get("target_company", "")
                    case_data.company_info.company_capital = CompanyInfo.format_capital(company_info.get("company_capital", ""))
                    case_data.company_info.company_establish = company_info.get("company_establish", "")
                    case_data.company_info.company_addr = company_info.get("company_addr", "")
                    case_data.company_info.company_reg = company_info.get("company_reg", "")
                    case_data.company_info.legal_representative = company_info.get("legal_representative", "")
                    case_data.company_info.company_cancel_apply = company_info.get("company_cancel_apply", "")
                    case_data.company_info.company_cancel_date = company_info.get("company_cancel_date", "")
                    case_data.company_info.cancel_doc = company_info.get("cancel_doc", "")
                    case_data.company_info.capital_status = company_info.get("capital_status", "")
                    case_data.company_info.subscribe_date = company_info.get("subscribe_date", "")

                    # 处理股东信息
                    shareholders = company_info.get("shareholders", [])
                    for i, sh in enumerate(shareholders):
                        if i < len(case_data.defendants):
                            case_data.defendants[i].def_name = sh.get("name", "")
                            case_data.defendants[i].def_share = sh.get("share", "")
                        else:
                            # 添加新的被告
                            new_def = DefendantInfo()
                            new_def.def_name = sh.get("name", "")
                            new_def.def_share = sh.get("share", "")
                            case_data.defendants.append(new_def)

        # 5. 处理身份证PDF（直接用规则解析，快速可靠）
        if "id_card_front" in files:
            for file_info in files["id_card_front"]:
                # 先尝试直接提取文本
                pdf_text = self.pdf_service.extract_text(file_info["path"])

                if not pdf_text.strip():
                    # 如果文本为空（扫描版PDF），使用OCR
                    print(f"[OCR] 身份证PDF文本为空，使用OCR: {file_info['filename']}")
                    pdf_text = self.pdf_service.extract_text_with_ocr(file_info["path"])

                id_info = {}
                if pdf_text and agent:
                    print(f"[身份证] 正在解析: {file_info['filename']}")
                    id_info = agent._parse_id_card_rules(pdf_text)

                    # 从文件名提取姓名（备用）
                    name_from_file = ""
                    if "_身份证" in file_info["filename"]:
                        name_from_file = file_info["filename"].split("_身份证")[0].split("_")[-1]

                    # 优先使用文件名作为姓名（更可靠）
                    if name_from_file:
                        id_info["def_name"] = name_from_file

                    # 查找匹配的被告（通过姓名或身份证号）
                    matched = False
                    for def_info in case_data.defendants:
                        # 通过姓名匹配
                        if id_info.get("def_name") and def_info.def_name == id_info.get("def_name"):
                            def_info.def_gender = id_info.get("def_gender", "") or def_info.def_gender
                            def_info.def_nation = id_info.get("def_nation", "") or def_info.def_nation
                            def_info.def_id = id_info.get("def_id", "") or def_info.def_id
                            def_info.def_addr = id_info.get("def_addr", "") or def_info.def_addr
                            matched = True
                            break
                        # 通过身份证号匹配
                        if id_info.get("def_id") and def_info.def_id == id_info.get("def_id"):
                            def_info.def_name = def_info.def_name or id_info.get("def_name", "")
                            def_info.def_gender = id_info.get("def_gender", "") or def_info.def_gender
                            def_info.def_nation = id_info.get("def_nation", "") or def_info.def_nation
                            def_info.def_addr = id_info.get("def_addr", "") or def_info.def_addr
                            matched = True
                            break

                    # 如果没有匹配，添加新被告
                    if not matched and id_info.get("def_name"):
                        case_data.defendants.append(DefendantInfo(
                            def_name=id_info.get("def_name", ""),
                            def_gender=id_info.get("def_gender", ""),
                            def_nation=id_info.get("def_nation", ""),
                            def_id=id_info.get("def_id", ""),
                            def_addr=id_info.get("def_addr", "")
                        ))

        return case_data

    def get_file_stats(self, folder_path: str) -> Dict:
        """获取文件夹中文件的统计信息（排除干扰文件）"""
        stats = {
            "total_files": 0,
            "by_type": {},
            "page_counts": {},
            "ignored_count": 0
        }

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if not os.path.isfile(file_path):
                continue

            file_type = self.classify_file(filename)

            # 统计被忽略的文件
            if file_type == "ignored":
                stats["ignored_count"] += 1
                continue

            stats["total_files"] += 1

            if file_type not in stats["by_type"]:
                stats["by_type"][file_type] = []
            stats["by_type"][file_type].append(filename)

            # 获取PDF页数
            if filename.lower().endswith(".pdf"):
                page_count = self.pdf_service.get_page_count(file_path)
                stats["page_counts"][filename] = page_count

        return stats
