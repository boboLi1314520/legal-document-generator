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
    end_date: Optional[str] = ""            # 截止日期(模板变量)
    start_date: Optional[str] = ""          # 截止日期+1天(模板变量)
    guarantee_amount: Optional[str] = ""           # 保全金额(本金+利息+罚息)
    guarantee_amount_rounded: Optional[str] = ""    # 取整保全金额

    class Config:
        json_schema_extra = {
            "example": {
                "loan_total": "290000.00",
                "principal": "263809.52",
                "interest": "20659.12",
                "penalty_cutoff": "12469.60",
                "cutoff_date": "2026年03月03日",
                "end_date": "2026年3月3日",
                "start_date": "2026年3月4日",
                "guarantee_amount": "296938.24",
                "guarantee_amount_rounded": "290000.00"
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

    def calculate_guarantee_amount_rounded(self) -> str:
        """计算取整保全金额
        规则：
        1. 向下取整到千位
        2. 千位数字 < 5：截断到万位；千位数字 >= 5：保留千位
        """
        amount_str = self.guarantee_amount or self.calculate_guarantee_amount()
        if not amount_str:
            return ""
        try:
            amount = float(amount_str)
            floor_value = int(amount // 1000) * 1000
            thousands_digit = (floor_value // 1000) % 10
            if thousands_digit < 5:
                result = (floor_value // 10000) * 10000
            else:
                result = floor_value
            return f"{result:.2f}"
        except (ValueError, TypeError):
            return ""
