"""
债务信息模型
"""
from pydantic import BaseModel
from typing import Optional


class DebtInfo(BaseModel):
    """债务信息"""
    loan_total: Optional[str] = ""          # 贷款本金合计
    principal: Optional[str] = ""           # 欠付本金
    interest: Optional[str] = ""            # 利息
    penalty_cutoff: Optional[str] = ""      # 截止日罚息
    cutoff_date: Optional[str] = ""         # 截止日期
    guarantee_amount: Optional[str] = ""    # 保全金额(本金+利息+罚息)

    class Config:
        json_schema_extra = {
            "example": {
                "loan_total": "290000.00",
                "principal": "263809.52",
                "interest": "20659.12",
                "penalty_cutoff": "12469.60",
                "cutoff_date": "2026年03月03日",
                "guarantee_amount": "296938.24"
            }
        }

    def calculate_guarantee_amount(self) -> str:
        """计算保全金额"""
        try:
            p = float(self.principal or 0)
            i = float(self.interest or 0)
            penalty = float(self.penalty_cutoff or 0)
            total = p + i + penalty
            return f"{total:.2f}"
        except ValueError:
            return ""
