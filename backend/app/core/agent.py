"""
法律 AI Agent - 增强版
支持解析公示系统PDF、身份证PDF等
"""
import os
import json
import re
import base64
from typing import Optional, Dict, List
from dotenv import load_dotenv
from ..models.company import CompanyInfo

load_dotenv()


class LegalAgent:
    """法律文书智能解析与生成 Agent"""

    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"

    async def _call_api(self, messages: list) -> str:
        """调用 DeepSeek API"""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    print(f"API 错误: {response.status_code} - {response.text}")
                    return ""
        except Exception as e:
            print(f"API 调用失败: {e}")
            return ""

    async def _call_vision_api(self, image_base64: str, prompt: str) -> str:
        """调用支持视觉的API（使用OpenAI兼容格式）

        DeepSeek Chat不支持图像输入，这里改用其他方案
        """
        # 方案1: 使用DeepSeek的chat模型处理文本
        # 方案2: 对于图像，我们使用开源OCR库
        return ""

    def ocr_image_local(self, image_path: str) -> Dict:
        """使用本地OCR库识别身份证图片

        使用RapidOCR（轻量级，已安装）
        """
        result = {
            "def_name": "",
            "def_gender": "",
            "def_nation": "",
            "def_id": "",
            "def_addr": ""
        }

        # 使用RapidOCR（推荐，轻量级）
        try:
            from rapidocr_onnxruntime import RapidOCR
            ocr = RapidOCR()
            ocr_result, elapse = ocr(image_path)  # 直接调用
            if ocr_result:
                all_text = []
                for line in ocr_result:
                    if line and len(line) >= 2:
                        # RapidOCR返回格式: [坐标, 文本, 置信度]
                        all_text.append(line[1])

                full_text = " ".join(all_text)
                print(f"RapidOCR识别结果: {full_text}")

                # 解析身份证信息
                result = self._parse_id_card_text(full_text)
        except Exception as e:
            print(f"RapidOCR失败: {e}")

        return result

    def _parse_id_card_text(self, text: str) -> Dict:
        """解析身份证OCR文本"""
        result = {
            "def_name": "",
            "def_gender": "",
            "def_nation": "",
            "def_id": "",
            "def_addr": ""
        }

        # 提取身份证号
        id_match = re.search(r'\d{17}[\dXx]', text)
        if id_match:
            result["def_id"] = id_match.group().upper()

        # 提取性别 - 处理OCR识别不完整的情况
        if "男" in text:
            result["def_gender"] = "男"
        elif "女" in text:
            result["def_gender"] = "女"

        # 提取民族 - 处理"民族汉"这种连续的情况
        nation_match = re.search(r'民族(汉|蒙古|回|藏|维吾尔|苗|彝|壮|布依|朝鲜|满|侗|瑶|白|土家|哈尼|哈萨克|傣|黎|傈僳|佤|畲|高山|拉祜|水|东乡|纳西|景颇|柯尔克孜|土|达斡尔|仫佬|羌|布朗|撒拉|毛南|仡佬|锡伯|阿昌|普米|塔吉克|怒|乌孜别克|俄罗斯|鄂温克|德昂|保安|裕固|京|塔塔尔|独龙|鄂伦春|赫哲|门巴|珞巴|基诺)', text)
        if nation_match:
            result["def_nation"] = nation_match.group(1)
        else:
            # 尝试标准匹配
            nation_match = re.search(r'(汉|蒙古|回|藏|维吾尔|苗|彝|壮|布依|朝鲜|满|侗|瑶|白|土家|哈尼|哈萨克|傣|黎|傈僳|佤|畲|高山|拉祜|水|东乡|纳西|景颇|柯尔克孜|土|达斡尔|仫佬|羌|布朗|撒拉|毛南|仡佬|锡伯|阿昌|普米|塔吉克|怒|乌孜别克|俄罗斯|鄂温克|德昂|保安|裕固|京|塔塔尔|独龙|鄂伦春|赫哲|门巴|珞巴|基诺)族', text)
            if nation_match:
                result["def_nation"] = nation_match.group(1)

        # 提取住址 - 处理OCR结果中"住址"和地址连在一起的情况
        # re.DOTALL: 让.匹配\n，地址可能跨多行
        # \d{17}[\dXx]: 身份证号作为终止标记，防止"公民身份"被OCR拆开
        addr_match = re.search(r'住址[：:]?\s*(.+?)(?=\s*\d{17}[\dXx]|公民身份|公民\s*身份|$)', text, re.DOTALL)
        if addr_match:
            addr = addr_match.group(1).strip()
            # 清理可能夹杂的换行符
            addr = addr.replace('\n', '').replace('\r', '')
            # 合并分散的地址信息
            # 处理"村266号"等地址片段
            village_match = re.search(r'(村[^住址公民身份]+)', text)
            if village_match:
                village_part = village_match.group(1)
                if village_part not in addr:
                    addr += village_part
            result["def_addr"] = addr
        else:
            # 尝试匹配省份开头的地址
            addr_match2 = re.search(r'([一-龥]{2,}省[一-龥\d]+)', text)
            if addr_match2:
                result["def_addr"] = addr_match2.group(1)

        # 提取姓名 - 多种格式处理
        # 格式1: "姓名陈荣" 连在一起
        name_match = re.search(r'姓名([一-龥]{2,4})', text)
        if name_match:
            result["def_name"] = name_match.group(1)
        else:
            # 格式2: 姓名单独一行
            # 扩展排除词列表
            exclude_words = ["姓名", "性别", "民族", "出生", "住址", "公民身份号码",
                             "别男", "别女", "族汉", "族回", "族满", "生19", "生20",
                             "性别男", "性别女",  # OCR可能识别出的组合词
                             "山东省", "河北省", "河南省", "江苏省", "浙江省", "广东省",
                             "湖南省", "湖北省", "四川省", "陕西省", "福建省"]

            lines = text.split()
            for line in lines:
                line = line.strip()
                if line and 2 <= len(line) <= 4:
                    if re.match(r'^[一-龥]+$', line):
                        if line not in exclude_words and not line.endswith('省'):
                            # 额外检查：不应该是"性别"+"男/女"的组合
                            if not re.match(r'^性别', line):
                                result["def_name"] = line
                                break

        return result

    async def parse_case(self, text: str) -> dict:
        """解析案件信息"""
        if not self.api_key or self.api_key == "your_api_key_here":
            return self._default_case_info(text)

        prompt = f"""请从以下法律文书中提取关键信息，以 JSON 格式返回。

要求提取的字段：
- plaintiff: 原告名称
- defendant: 被告名称
- case_type: 案件类型（如：借贷纠纷、合同纠纷等）
- amount: 标的金额
- facts: 案件事实摘要（200字以内）
- evidence: 证据列表（数组）
- court: 受理法院

法律文书内容：
{text[:2000]}

请直接返回 JSON 格式数据，不要添加任何说明文字。"""

        messages = [{"role": "user", "content": prompt}]
        result = await self._call_api(messages)

        try:
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            return json.loads(result.strip())
        except:
            return self._default_case_info(text)

    def _default_case_info(self, text: str) -> dict:
        """生成默认案件信息"""
        plaintiff = ""
        defendant = ""

        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if "原告" in line and not plaintiff:
                plaintiff = line.replace("原告", "").replace("：", "").replace(":", "").strip()[:50]
            if "被告" in line and not defendant:
                defendant = line.replace("被告", "").replace("：", "").replace(":", "").strip()[:50]

        return {
            "plaintiff": plaintiff or "待识别",
            "defendant": defendant or "待识别",
            "case_type": "待识别",
            "amount": "",
            "facts": text[:200] if text else "",
            "evidence": [],
            "court": ""
        }

    async def parse_public_report(self, text: str) -> dict:
        """解析企业信用信息公示报告

        提取字段：
        - target_company: 企业名称
        - company_capital: 注册资本
        - company_establish: 成立日期
        - company_addr: 住所
        - company_reg: 登记机关
        - legal_representative: 法定代表人
        - shareholders: 股东列表 [{name, share}]
        - company_cancel_apply: 核准日期
        """
        if not self.api_key or self.api_key == "your_api_key_here":
            return self._parse_public_report_rules(text)

        prompt = f"""请从以下企业信用信息公示报告中提取关键信息，以 JSON 格式返回。

要求提取的字段：
- target_company: 企业名称
- company_capital: 注册资本
- company_establish: 成立日期
- company_addr: 住所
- company_reg: 登记机关
- legal_representative: 法定代表人姓名
- shareholders: 股东列表，数组格式，每个元素包含 name(股东姓名) 和 share(持股比例)
- company_cancel_apply: 注销核准日期
- capital_status: 股东出资状态（"未实缴" 或 "已实缴"）
- subscribe_date: 股东认缴出资日期

公示报告内容：
{text[:4000]}

请直接返回 JSON 格式数据，不要添加任何说明文字。如果某个字段无法提取，请返回空字符串。"""

        messages = [{"role": "user", "content": prompt}]
        result = await self._call_api(messages)

        try:
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            return json.loads(result.strip())
        except:
            return self._parse_public_report_rules(text)

    def _parse_public_report_rules(self, text: str) -> dict:
        """规则方式解析公示报告（备用）"""
        result = {
            "target_company": "",
            "company_capital": "",
            "company_establish": "",
            "company_addr": "",
            "company_reg": "",
            "legal_representative": "",
            "shareholders": [],
            "company_cancel_apply": "",
            "company_cancel_date": "",
            "capital_status": "",
            "subscribe_date": ""
        }

        lines = text.split("\n")

        # 首先尝试从营业执照信息部分提取（按位置解析）
        in_license_section = False
        license_lines = []
        for i, line in enumerate(lines):
            line = line.strip()

            # 进入营业执照信息区域
            if "营业执照信息" in line or "公示" in line:
                in_license_section = True
                continue

            # 收集营业执照区域的行
            if in_license_section:
                if line and len(line) > 2:
                    # 遇到其他区域标题则停止
                    if "信息" in line and "营业执照" not in line and "股东" not in line and "公示" not in line:
                        break
                    license_lines.append(line)

        # 调试输出
        print(f"[公示解析] 找到 {len(license_lines)} 行营业执照数据")
        for idx, ln in enumerate(license_lines):
            print(f"  [{idx}]: {ln}")

        # 按关键词-值对解析（更可靠）
        # 格式通常是：标签: 值 或 标签 值
        i = 0
        while i < len(license_lines):
            line = license_lines[i]

            # 统一社会信用代码（18位代码）
            if re.match(r'^[\dA-Z]{18}$', line):
                result["company_id"] = line
                print(f"[公示解析] 信用代码: {result['company_id']}")

            # 企业名称（包含"公司"）
            elif "公司" in line and not result["target_company"]:
                result["target_company"] = line
                print(f"[公示解析] 企业名称: {result['target_company']}")

            # 有限责任公司/公司类型（跳过）
            elif "有限" in line and "责任" in line:
                pass

            # 注册资本（包含"万"）
            elif re.search(r'\d+\.?\d*万', line) and not result["company_capital"]:
                capital_match = re.search(r'([\d\.]+万)', line)
                if capital_match:
                    result["company_capital"] = CompanyInfo.format_capital(capital_match.group(1))
                    print(f"[公示解析] 注册资本: {result['company_capital']}")

            # 登记机关（包含"市场监督"或"管理局"）
            elif ("市场监督" in line or "管理局" in line) and not result["company_reg"]:
                result["company_reg"] = line
                print(f"[公示解析] 登记机关: {result['company_reg']}")

            # 住所（包含省/市/区/县/镇/村等行政区划，或路/街/道/号/房/栋等地址特征）
            elif re.search(r'[省市县区镇乡村街道路号房栋]', line) and not result["company_addr"]:
                if "市场监督" not in line and "管理" not in line and "有限" not in line and "责任" not in line:
                    result["company_addr"] = line
                    print(f"[公示解析] 住所: {result['company_addr']}")

            # 日期格式 - 需要根据上下文判断是成立日期还是核准日期
            elif re.match(r'^\d{4}年\d{1,2}月\d{1,2}日$', line):
                # 第一个日期是成立日期
                if not result["company_establish"]:
                    result["company_establish"] = line
                    print(f"[公示解析] 成立日期: {result['company_establish']}")
                # 第二个日期是核准日期
                elif not result["company_cancel_apply"]:
                    result["company_cancel_apply"] = line
                    print(f"[公示解析] 核准日期: {result['company_cancel_apply']}")

            # 法定代表人（纯中文姓名，2-4个字）
            elif re.match(r'^[一-龥]{2,4}$', line) and not result["legal_representative"]:
                result["legal_representative"] = line
                print(f"[公示解析] 法定代表人: {result['legal_representative']}")

            i += 1

        # 备用提取方式：关键词匹配
        for i, line in enumerate(lines):
            line = line.strip()

            # 企业名称 - 如果上面没找到
            if not result["target_company"] and "公司" in line:
                company_match = re.search(r'([一-龥]+公司)', line)
                if company_match and "营业执照" not in line:
                    result["target_company"] = company_match.group(1)

            # 统一社会信用代码
            if "统一社会信用代码" in line:
                match = re.search(r'[\dA-Z]{18}', line)
                if match:
                    result["company_id"] = match.group()

            # 注册资本 - 查找数字+万/元
            if not result["company_capital"]:
                if "注册资本" in line or ("万" in line and re.search(r'\d+\.?\d*万', line)):
                    match = re.search(r'([\d\.]+万)', line)
                    if match:
                        result["company_capital"] = CompanyInfo.format_capital(match.group(1))

            # 成立日期 - 如果上面没找到
            if not result["company_establish"] and "成立日期" in line:
                match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', line)
                if match:
                    result["company_establish"] = match.group(1)
                elif i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', next_line)
                    if match:
                        result["company_establish"] = match.group(1)

            # 住所 - 关键词匹配
            if not result["company_addr"] and "住所" in line:
                addr = re.sub(r'住所[：:]?\s*', '', line).strip()
                if addr and len(addr) > 5:
                    result["company_addr"] = addr

            # 法定代表人 - 如果上面没找到
            if not result["legal_representative"]:
                if "法定代表人" in line or ("法人" in line and "代表" not in line):
                    match = re.search(r'(法定代表人|法人)[：:]\s*(\S+)', line)
                    if match:
                        result["legal_representative"] = match.group(2)
                    else:
                        # 检查下一行
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and 2 <= len(next_line) <= 4:
                                if re.match(r'^[一-龥]+$', next_line):
                                    result["legal_representative"] = next_line

            # 登记机关 - 关键词匹配
            if not result["company_reg"] and "登记机关" in line:
                value = re.sub(r'登记机关[：:]?\s*', '', line).strip()
                if value:
                    result["company_reg"] = value
                elif i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if "市场监督" in next_line or "管理局" in next_line:
                        result["company_reg"] = next_line

            # 注销日期（独立的注销日期字段）
            if "注销日期" in line or "注销日期：" in line:
                match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', line)
                if match:
                    result["company_cancel_date"] = match.group(1)
                    print(f"[公示解析] 注销日期: {result['company_cancel_date']}")

        # 提取股东信息 - 从股东表格区域
        in_shareholder_section = False
        for i, line in enumerate(lines):
            line = line.strip()

            if "股东及出资信息" in line or "股东名称" in line:
                in_shareholder_section = True
                continue

            if in_shareholder_section:
                # 跳过表头
                if line in ["序号", "股东名称", "股东类型", "证照/证件类型", "证照/证件号码", "详情", "查看", "非公示项", "自然人股东"]:
                    continue

                # 跳过数字序号
                if re.match(r'^\d+$', line):
                    continue

                # 跳过其他区域标题
                if "信息" in line and "股东" not in line:
                    in_shareholder_section = False
                    continue

                # 匹配中文姓名（2-4个汉字）
                if line and 2 <= len(line) <= 4:
                    if re.match(r'^[一-龥]+$', line):
                        # 检查是否已经存在
                        existing = [s["name"] for s in result["shareholders"]]
                        if line not in existing:
                            result["shareholders"].append({
                                "name": line,
                                "share": ""
                            })
                        if len(result["shareholders"]) >= 5:
                            break

        return result

    def _build_ocr_grid(self, blocks: list, row_tolerance: float = 30) -> list:
        """将OCR文本块按Y坐标分组为行列网格

        Args:
            blocks: OCR结果列表 [{"text", "cx", "cy", "x", "y", "width", "height"}, ...]
            row_tolerance: 同行Y坐标容差（像素）

        Returns:
            二维数组 grid[row][col]，每行按X坐标排序
        """
        if not blocks:
            return []

        # 按Y坐标排序
        sorted_blocks = sorted(blocks, key=lambda b: b.get("cy", 0))

        # 分组为行
        rows = []
        current_row = [sorted_blocks[0]]
        current_cy = sorted_blocks[0].get("cy", 0)

        for block in sorted_blocks[1:]:
            cy = block.get("cy", 0)
            if abs(cy - current_cy) <= row_tolerance:
                current_row.append(block)
            else:
                rows.append(current_row)
                current_row = [block]
                current_cy = cy
        rows.append(current_row)

        # 每行内按X坐标排序
        grid = []
        for row in rows:
            row_sorted = sorted(row, key=lambda b: b.get("x", 0))
            grid.append([b["text"] for b in row_sorted])

        # 打印调试信息
        print(f"[OCR网格] 共{len(grid)}行")
        for r, row in enumerate(grid):
            print(f"  行{r}: {row}")

        return grid

    @staticmethod
    def _clean_company_reg(val: str) -> str:
        """清洗登记机关文本：去掉前缀标签、后缀登记状态"""
        val = re.sub(r'登记机关[：:]\s*', '', val)
        val = re.sub(r'\s*登记状态[：:].*$', '', val)
        return val.strip()

    def _extract_field(self, grid: list, labels: list, value_pattern: str = None) -> str:
        """扫描grid，找到含labels中任一关键词的行，返回该标签后的值

        策略：
        1. 先尝试从标签所在列的下一列取值
        2. 再尝试从该行文本中正则提取
        """
        for row_cells in grid:
            row_text = " ".join(row_cells)
            for label in labels:
                if label not in row_text:
                    continue
                # 策略1：标签所在列的下一个单元格
                for i, cell in enumerate(row_cells):
                    if label in cell and i + 1 < len(row_cells):
                        val = row_cells[i + 1].strip()
                        if val and label not in val:
                            # 如果指定了value_pattern，验证一下
                            if value_pattern:
                                m = re.search(value_pattern, val)
                                if m:
                                    return m.group(0)
                                break  # 不匹配，跳出内层循环尝试策略2
                            return val
                # 策略2：从整行正则提取 label：value
                m = re.search(label + r'[：:]?\s*(.+)', row_text)
                if m:
                    val = m.group(1).strip()
                    if val and len(val) > 0:
                        if value_pattern:
                            pm = re.search(value_pattern, val)
                            if pm:
                                return pm.group(0)
                            break
                        return val
                break  # label matched row but couldn't extract, stop trying labels
        return ""

    PAGINATION_WORDS = {"首页", "上一页", "下一页", "尾页", "第", "跳转", "页"}

    def _parse_business_license(self, grid: list, raw_text: str = "") -> dict:
        """从营业执照信息照片的OCR网格中提取公司信息

        使用关键词扫描替代硬编码位置，适应不同布局。
        列布局：奇数列=标签，偶数列=值。
        """
        result = {
            "target_company": "",
            "legal_representative": "",
            "company_establish": "",
            "company_cancel_apply": "",
            "company_capital": "",
            "company_reg": "",
            "company_addr": "",
            "shareholder_names": [],
            "company_id": ""
        }

        # ===== 关键词扫描提取 =====
        result["company_id"] = self._extract_field(grid, ["统一社会信用代码"], r'[A-Z0-9]{18}')
        result["target_company"] = self._extract_field(grid, ["企业名称", "公司名称"])
        result["legal_representative"] = self._extract_field(grid, ["法定代表人"], r'[一-龥]{2,4}')
        result["company_establish"] = self._extract_field(grid, ["成立日期"], r'\d{4}年\d{1,2}月\d{1,2}日')
        result["company_cancel_apply"] = self._extract_field(grid, ["核准日期"], r'\d{4}年\d{1,2}月\d{1,2}日')

        # 注册资本
        cap_val = self._extract_field(grid, ["注册资本"])
        if cap_val:
            cap_match = re.search(r'([\d\.]+万)', cap_val)
            if cap_match:
                result["company_capital"] = CompanyInfo.format_capital(cap_match.group(1))
                print(f"[营业执照解析] 注册资本: {result['company_capital']}")

        # 登记机关（需清洗前缀/后缀）
        reg_val = self._extract_field(grid, ["登记机关"])
        if reg_val:
            result["company_reg"] = self._clean_company_reg(reg_val)
            print(f"[营业执照解析] 登记机关: {result['company_reg']}")

        # 住所
        addr_val = self._extract_field(grid, ["住所"])
        if addr_val and re.search(r'[省市县区镇乡村街道路号房栋]', addr_val):
            result["company_addr"] = addr_val
            print(f"[营业执照解析] 住所: {result['company_addr']}")

        # ===== 收集所有日期，回退公司日期字段 =====
        all_text_lines = [" ".join(row) for row in grid]
        full_text = "\n".join(all_text_lines)

        dates = re.findall(r'\d{4}年\d{1,2}月\d{1,2}日', full_text)
        unique_dates = list(dict.fromkeys(dates))
        print(f"[营业执照解析] 找到日期: {unique_dates}")

        if not result["company_establish"] and len(unique_dates) >= 1:
            result["company_establish"] = unique_dates[0]
            print(f"[营业执照解析] 成立日期(回退): {unique_dates[0]}")
        if not result["company_cancel_apply"] and len(unique_dates) >= 2:
            result["company_cancel_apply"] = unique_dates[1]
            print(f"[营业执照解析] 核准日期(回退): {unique_dates[1]}")

        # 企业名称回退：找含"公司"的行
        if not result["target_company"]:
            for line in all_text_lines:
                if "公司" in line:
                    match = re.search(r'([一-龥]+有限公司|[一-龥]+有限责任公司)', line)
                    if match:
                        result["target_company"] = match.group(1)
                        print(f"[营业执照解析] 企业名称(回退): {result['target_company']}")
                        break

        # 法定代表人回退
        if not result["legal_representative"]:
            for line in all_text_lines:
                if "法定代表人" in line:
                    match = re.search(r'法定代表人[：:]?\s*([一-龥]{2,4})', line)
                    if match:
                        result["legal_representative"] = match.group(1)
                        print(f"[营业执照解析] 法定代表人(回退): {result['legal_representative']}")
                        break

        # 注册资本回退
        if not result["company_capital"]:
            for line in all_text_lines:
                cap_match = re.search(r'([\d\.]+万)', line)
                if cap_match:
                    result["company_capital"] = CompanyInfo.format_capital(cap_match.group(1))
                    print(f"[营业执照解析] 注册资本(回退): {result['company_capital']}")
                    break

        # 登记机关回退
        if not result["company_reg"]:
            for line in all_text_lines:
                if "市场监督" in line or "管理局" in line:
                    result["company_reg"] = self._clean_company_reg(line.strip())
                    print(f"[营业执照解析] 登记机关(回退): {result['company_reg']}")
                    break

        # 住所回退
        if not result["company_addr"]:
            for line in all_text_lines:
                if "住所" in line:
                    addr = re.sub(r'住所[：:]?\s*', '', line).strip()
                    if addr and len(addr) > 5:
                        result["company_addr"] = addr
                        print(f"[营业执照解析] 住所(回退): {addr}")
                        break

        # ===== 股东名称提取 =====
        # 找到"股东及出资信息"表格，从下一行开始提取名称
        in_shareholder = False
        for row_idx, row in enumerate(grid):
            row_text = " ".join(row)
            # 检查分页终止条件
            if "共查询" in row_text or "首页" in row_text:
                in_shareholder = False
                break

            if "股东及出资信息" in row_text or "股东名称" in row_text:
                in_shareholder = True
                print(f"[营业执照解析] 进入股东表格(行{row_idx}): {row_text}")
                continue

            if in_shareholder and len(row) >= 2:
                # 股东名称通常在表头后的第2列
                # 格式：['序号', '股东名称', '股东类型', ...] → 股东名称在col1
                # 数据行：['张纪超', '自然人股东', ...] → 名称在col0
                # 尝试从第1列或第2列提取
                for col_idx in [0, 1]:
                    if col_idx < len(row):
                        col_val = row[col_idx].strip()
                        if not col_val or col_val.isdigit() or len(col_val) <= 1:
                            continue
                        if col_val in ["股东名称", "序号", "认缴出资额", "实缴出资额", "认缴出资日期",
                                        "股东类型", "证照/证照号码", "非公示项", "自然人股东", "详情", "查看"]:
                            continue
                        if col_val in self.PAGINATION_WORDS:
                            continue
                        if any(w in col_val for w in self.PAGINATION_WORDS):
                            continue
                        # 名称：2-4个中文字符
                        names = re.split(r'[、,，\s]+', col_val)
                        for name in names:
                            name = name.strip()
                            if name and 2 <= len(name) <= 4 and re.match(r'^[一-龥]+$', name):
                                if name not in result["shareholder_names"]:
                                    result["shareholder_names"].append(name)
                                    print(f"[营业执照解析] 股东: {name}")
                        break  # 从当前行提取到一个即可

        print(f"[营业执照解析] 结果: {json.dumps(result, ensure_ascii=False)}")
        return result

    def _parse_shareholder_detail(self, grid: list, raw_text: str = "") -> dict:
        """从股东及出资详细信息照片的OCR网格中提取股东详情

        网格布局（实际OCR输出）：
        Row 0: ['股东及出资详细信息']
        Row 1: ['股东信息']              ← 第一个表格标题
        Row 2: ['股东名称', '张纪超']    ← 数据行：名称
        Row 3: ['认缴额(万元)', '40']    ← 数据行：认缴额
        Row 4: ['实缴额（万元）']         ← 数据行：实缴额（可能为空）
        Row 5: ['认缴明细信息']          ← 第二个表格标题
        Row 6: ['认缴出资方式', '认缴出资额（万元）', '认缴出资日期']  ← 列头
        Row 7: ['货币', '40', '2051年1月1日']  ← 数据行：认缴日期

        Returns:
            {"name": "张纪超", "share": "40", "subscribe_date": "2051年1月1日", "paid_amount": "0"}
        """
        result = {
            "name": "",
            "share": "",
            "paid_amount": "",
            "subscribe_date": ""
        }

        def safe_get(row, col):
            if 0 < row <= len(grid) and 0 < col <= len(grid[row - 1]):
                val = grid[row - 1][col - 1]
                if val:
                    return val
            return ""

        all_text = [" ".join(row) for row in grid]
        full_text = "\n".join(all_text)
        print(f"[股东详情解析] 共{len(grid)}行: {all_text[:5]}...")

        # 查找"股东信息"行 → 数据从下一行开始
        shareholder_data_start = -1
        subscription_data_start = -1

        for r, row in enumerate(grid):
            row_text = " ".join(row)
            if "股东信息" in row_text and shareholder_data_start < 0:
                shareholder_data_start = r + 2  # 跳过标题行，指向数据行（1-based）
            if "认缴明细" in row_text and subscription_data_start < 0:
                subscription_data_start = r + 3  # 跳过标题行+列头行，指向数据行（1-based）

        # 股东名称
        if shareholder_data_start > 0:
            val = safe_get(shareholder_data_start, 2)  # 第2列是名称值
            if val and 2 <= len(val) <= 4 and re.match(r'^[一-龥]+$', val):
                result["name"] = val
                print(f"[股东详情] 名称: {val}")

            # 认缴额
            val = safe_get(shareholder_data_start + 1, 2)
            if val:
                amount_match = re.search(r'(\d+\.?\d*)', val)
                if amount_match:
                    result["share"] = amount_match.group(1)
                    print(f"[股东详情] 认缴额: {result['share']}万元")

            # 实缴额
            val = safe_get(shareholder_data_start + 2, 2)
            if val:
                amount_match = re.search(r'(\d+\.?\d*)', val)
                if amount_match:
                    result["paid_amount"] = amount_match.group(1)
                    print(f"[股东详情] 实缴额: {result['paid_amount']}万元")
                else:
                    result["paid_amount"] = "0"
            else:
                result["paid_amount"] = "0"
                print(f"[股东详情] 实缴额: 为空，默认0")

        # 认缴出资日期
        if subscription_data_start > 0:
            val = safe_get(subscription_data_start, 3)  # 第3列是日期值
            if val:
                date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', val)
                if date_match:
                    result["subscribe_date"] = date_match.group(1)
                    print(f"[股东详情] 认缴日期: {result['subscribe_date']}")

        # 关键词回退
        if not result["name"]:
            for line in all_text:
                if "股东" in line and "信息" not in line and "出资" not in line:
                    name_match = re.search(r'([一-龥]{2,4})', line)
                    if name_match and name_match.group(1) not in ["股东名称", "股东"]:
                        result["name"] = name_match.group(1)
                        print(f"[股东详情] 名称(回退): {result['name']}")
                        break

        if not result["share"]:
            share_match = re.search(r'认缴额[：:(（]?\s*(\d+\.?\d*)', full_text)
            if share_match:
                result["share"] = share_match.group(1)
                print(f"[股东详情] 认缴额(回退): {result['share']}万元")

        if not result["paid_amount"]:
            paid_match = re.search(r'实缴额[：:(（]?\s*(\d+\.?\d*)', full_text)
            if paid_match:
                result["paid_amount"] = paid_match.group(1)
                print(f"[股东详情] 实缴额(回退): {result['paid_amount']}万元")
            else:
                result["paid_amount"] = "0"

        if not result["subscribe_date"]:
            date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', full_text)
            if date_match:
                result["subscribe_date"] = date_match.group(1)
                print(f"[股东详情] 认缴日期(回退): {result['subscribe_date']}")

        print(f"[股东详情] 结果: {json.dumps(result, ensure_ascii=False)}")
        return result

    async def parse_id_card(self, text: str) -> dict:
        """解析身份证PDF

        提取字段：
        - def_name: 姓名
        - def_gender: 性别
        - def_nation: 民族
        - def_id: 公民身份号码
        - def_addr: 住址
        """
        if not self.api_key or self.api_key == "your_api_key_here":
            return self._parse_id_card_rules(text)

        prompt = f"""请从以下身份证文本中提取信息，以 JSON 格式返回。

要求提取的字段：
- def_name: 姓名
- def_gender: 性别（男/女）
- def_nation: 民族（如：汉、回、满等）
- def_id: 公民身份号码（18位）
- def_addr: 住址

身份证内容：
{text[:1000]}

请直接返回 JSON 格式数据，不要添加任何说明文字。"""

        messages = [{"role": "user", "content": prompt}]
        result = await self._call_api(messages)

        try:
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            return json.loads(result.strip())
        except:
            return self._parse_id_card_rules(text)

    def _parse_id_card_rules(self, text: str) -> dict:
        """规则方式解析身份证（备用）"""
        result = {
            "def_name": "",
            "def_gender": "",
            "def_nation": "",
            "def_id": "",
            "def_addr": ""
        }

        # 提取身份证号
        id_match = re.search(r'\d{17}[\dXx]', text)
        if id_match:
            result["def_id"] = id_match.group().upper()

        # 提取性别
        if "男" in text:
            result["def_gender"] = "男"
        elif "女" in text:
            result["def_gender"] = "女"

        # 提取民族
        # 格式1: "民族汉" 连在一起
        nation_match = re.search(r'民族(汉|蒙古|回|藏|维吾尔|苗|彝|壮|布依|朝鲜|满|侗|瑶|白|土家|哈尼|哈萨克|傣|黎|傈僳|佤|畲|高山|拉祜|水|东乡|纳西|景颇|柯尔克孜|土|达斡尔|仫佬|羌|布朗|撒拉|毛南|仡佬|锡伯|阿昌|普米|塔吉克|怒|乌孜别克|俄罗斯|鄂温克|德昂|保安|裕固|京|塔塔尔|独龙|鄂伦春|赫哲|门巴|珞巴|基诺)', text)
        if nation_match:
            result["def_nation"] = nation_match.group(1)
        else:
            # 格式2: "汉族" 标准格式
            nation_match = re.search(r'(汉|蒙古|回|藏|维吾尔|苗|彝|壮|布依|朝鲜|满|侗|瑶|白|土家|哈尼|哈萨克|傣|黎|傈|傈僳|佤|畲|高山|拉祜|水|东乡|纳西|景颇|柯尔克孜|土|达斡尔|仫佬|羌|布朗|撒拉|毛南|仡佬|锡伯|阿昌|普米|塔吉克|怒|乌孜别克|俄罗斯|鄂温克|德昂|保安|裕固|京|塔塔尔|独龙|鄂伦春|赫哲|门巴|珞巴|基诺)族', text)
            if nation_match:
                result["def_nation"] = nation_match.group(1)

        # 提取姓名 - 优先匹配"姓名XXX"格式
        name_match = re.search(r'姓名([一-龥]{2,4})', text)
        if name_match:
            result["def_name"] = name_match.group(1)
        else:
            # 备用：查找纯中文姓名
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                if line and 2 <= len(line) <= 4:
                    # 跳过包含特定关键词的行
                    if any(kw in line for kw in ["姓", "名", "性别", "民族", "出生", "住址", "公民", "身份", "号码"]):
                        continue
                    if not re.search(r'[\dXx]', line):  # 不包含数字
                        if re.match(r'^[一-龥]+$', line):  # 纯中文
                            result["def_name"] = line
                            break

        # 提取住址
        # re.DOTALL: 让.匹配\n，地址可能跨多行
        # \d{17}[\dXx]: 身份证号作为终止标记，防止"公民身份"被OCR拆开
        addr_match = re.search(r'住址[：:]?\s*(.+?)(?=\s*\d{17}[\dXx]|公民身份|公民\s*身份|\n公民|$)', text, re.DOTALL)
        if addr_match:
            addr = addr_match.group(1).strip()
            # 清理可能夹杂的换行符
            addr = addr.replace('\n', '').replace('\r', '')
            # 合并地址片段
            village_match = re.search(r'(村[^住址公民身份\n]+)', text)
            if village_match:
                village_part = village_match.group(1)
                if village_part not in addr:
                    addr += village_part
            result["def_addr"] = addr
        else:
            # 尝试匹配省份开头的地址
            addr_match2 = re.search(r'([一-龥]{2,}省[一-龥]+)', text)
            if addr_match2:
                result["def_addr"] = addr_match2.group(1)

        return result

    async def generate_complaint(self, case: dict) -> str:
        """生成起诉状内容"""
        if not self.api_key or self.api_key == "your_api_key_here":
            return case.get("facts", "待填写案件事实")

        prompt = f"""请根据以下案件信息，撰写民事起诉状的"事实与理由"部分。

案件信息：
- 原告：{case.get('plaintiff', '')}
- 被告：{case.get('defendant', '')}
- 案件类型：{case.get('case_type', '')}
- 标的额：{case.get('amount', '')}
- 案件事实：{case.get('facts', '')}

要求：
1. 语言规范、逻辑清晰
2. 引用相关法律条文
3. 字数在 300-500 字

请直接输出事实与理由内容，不要添加标题。"""

        messages = [{"role": "user", "content": prompt}]
        return await self._call_api(messages)

    async def generate_application(self, case: dict) -> str:
        """生成申请书内容"""
        if not self.api_key or self.api_key == "your_api_key_here":
            return case.get("facts", "待填写申请理由")

        prompt = f"""请根据以下案件信息，撰写申请书的"事实与理由"部分。

案件信息：
- 申请人：{case.get('plaintiff', '')}
- 被申请人：{case.get('defendant', '')}
- 案件类型：{case.get('case_type', '')}
- 案件事实：{case.get('facts', '')}

要求：
1. 语言规范、逻辑清晰
2. 字数在 200-400 字

请直接输出事实与理由内容。"""

        messages = [{"role": "user", "content": prompt}]
        return await self._call_api(messages)

    def recommend_court(self, addr: str) -> str:
        """根据地址推荐管辖法院

        规则：根据被告住所地确定基层人民法院
        """
        # 提取省市区县信息
        court = ""

        # 匹配省份和城市
        province_match = re.search(r'([一-龥]+省|[一-龥]+自治区|北京|上海|天津|重庆)', addr)
        city_match = re.search(r'([一-龥]+市|[一-龥]+自治州)', addr)
        district_match = re.search(r'([一-龥]+区|[一-龥]+县|[一-龥]+市)', addr)

        if district_match:
            district = district_match.group(1)
            court = f"{district}人民法院"
        elif city_match:
            city = city_match.group(1)
            court = f"{city}人民法院"
        elif province_match:
            province = province_match.group(1)
            court = f"{province}人民法院"

        return court or "XX人民法院"
