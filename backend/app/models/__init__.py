"""
数据模型
"""
from .company import CompanyInfo
from .defendant import DefendantInfo
from .loan import LoanContracts, QuotaContract, LoanContract
from .debt import DebtInfo
from .case import CaseData

__all__ = [
    "CompanyInfo",
    "DefendantInfo",
    "LoanContracts",
    "QuotaContract",
    "LoanContract",
    "DebtInfo",
    "CaseData"
]
