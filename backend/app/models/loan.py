"""
借贷合同模型
"""
from pydantic import BaseModel
from typing import Optional, List


class QuotaContract(BaseModel):
    """额度合同"""
    contract_no: Optional[str] = ""     # 合同编号
    contract_date: Optional[str] = ""   # 签订日期

    class Config:
        json_schema_extra = {
            "example": {
                "contract_no": "QYDED20200726012004",
                "contract_date": "2020年07月26日"
            }
        }


class LoanContract(BaseModel):
    """借款合同/借据"""
    jieju_no: Optional[str] = ""              # 借据号（JH开头）
    contract_no: Optional[str] = ""           # 合同编号（GHDJ开头）
    contract_date: Optional[str] = ""         # 签订日期
    principal: Optional[str] = ""             # 贷款本金
    rate: Optional[str] = ""                  # 实际利率
    penalty_rate: Optional[str] = ""          # 罚息利率
    standard_penalty_rate: Optional[str] = "" # 规范罚息利率(最高24%)
    periods: Optional[str] = ""               # 期数
    due_date: Optional[str] = ""              # 借据到期日期
    apply_date: Optional[str] = ""            # 申请日期
    total_principal: Optional[str] = ""       # 欠款总本金

    class Config:
        json_schema_extra = {
            "example": {
                "jieju_no": "JH20240708XS0M00012078",
                "contract_no": "GHDJJXS0240708001877549",
                "contract_date": "2024年07月08日",
                "principal": "10000.00",
                "rate": "12.93%",
                "penalty_rate": "19.39%",
                "standard_penalty_rate": "19.39%",
                "periods": "24",
                "due_date": "2026/07/08",
                "apply_date": "2026/03/03",
                "total_principal": "6666.64"
            }
        }


class LoanContracts(BaseModel):
    """借贷合同汇总"""
    quota_contracts: List[QuotaContract] = []  # 额度合同列表
    loan_contracts: List[LoanContract] = []    # 借款合同列表
    quota_count: int = 0                        # 额度合同总份数
    loan_count: int = 0                         # 借款合同总份数

    class Config:
        json_schema_extra = {
            "example": {
                "quota_contracts": [
                    {"contract_no": "EDXS0240708001677390", "contract_date": "2024年07月08日"}
                ],
                "loan_contracts": [
                    {
                        "jieju_no": "JH20240708XS0M00012078",
                        "contract_no": "GHDJJXS0240708001877549",
                        "contract_date": "2024年07月08日",
                        "principal": "10000.00",
                        "periods": "24",
                        "rate": "12.93%",
                        "penalty_rate": "19.39%",
                        "apply_date": "2026/03/03",
                        "total_principal": "6666.64"
                    }
                ],
                "quota_count": 1,
                "loan_count": 6
            }
        }
