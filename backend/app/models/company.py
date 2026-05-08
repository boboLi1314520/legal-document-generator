"""
公司信息模型
"""
from pydantic import BaseModel
from typing import Optional


class CompanyInfo(BaseModel):
    """公司基本信息"""
    target_company: Optional[str] = ""  # 企业名称
    company_abbr: Optional[str] = ""     # 公司简称
    company_capital: Optional[str] = ""  # 注册资本
    company_establish: Optional[str] = ""  # 成立日期
    company_cancel_apply: Optional[str] = ""  # 核准日期/申请日期
    company_cancel_date: Optional[str] = ""   # 注销日期
    legal_representative: Optional[str] = ""  # 法定代表人
    company_addr: Optional[str] = ""       # 住所
    company_reg: Optional[str] = ""        # 登记机关
    company_id: Optional[str] = ""         # 统一社会信用代码
    cancel_doc: Optional[str] = ""         # 注销文件类型（清算报告/简易注销全体投资人承诺书）
    capital_status: Optional[str] = ""     # 股东出资状态（未实缴/已实缴）
    subscribe_date: Optional[str] = ""     # 股东认缴出资日期

    class Config:
        json_schema_extra = {
            "example": {
                "target_company": "长沙纽威机电科技有限公司",
                "company_abbr": "纽威机电",
                "company_capital": "100万元",
                "company_establish": "2020年01月15日",
                "company_cancel_apply": "2024年03月20日",
                "company_cancel_date": "2024年03月25日",
                "legal_representative": "陈荣",
                "company_addr": "湖南省长沙市雨花区XX路XX号",
                "company_reg": "长沙市雨花区市场监督管理局",
                "company_id": "91430111053895688C",
                "cancel_doc": "简易注销全体投资人承诺书",
                "capital_status": "未实缴",
                "subscribe_date": "2025年01月15日"
            }
        }
