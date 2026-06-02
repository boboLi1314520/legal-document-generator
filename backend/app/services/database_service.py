"""
数据库服务 - JSON文件存储
"""
import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from ..models.case import CaseData
from ..models.company import CompanyInfo
from ..models.defendant import DefendantInfo
from ..models.loan import LoanContracts, LoanContract, QuotaContract
from ..models.debt import DebtInfo


class DatabaseService:
    """JSON文件存储服务"""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            # 默认存储在 backend/outputs/cases/
            base_dir = os.path.join(os.path.dirname(__file__), "../../outputs/cases")
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_case_path(self, case_id: str) -> Path:
        """获取案件JSON文件路径"""
        return self.base_dir / f"{case_id}.json"

    def save_case(self, case_data: CaseData) -> bool:
        """保存案件数据到JSON文件"""
        try:
            case_data.updated_at = datetime.now().isoformat()
            file_path = self._get_case_path(case_data.id)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(case_data.model_dump(), f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"保存案件数据失败: {e}")
            return False

    def load_case(self, case_id: str) -> Optional[CaseData]:
        """从JSON文件加载案件数据"""
        try:
            file_path = self._get_case_path(case_id)

            if not file_path.exists():
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 兼容存量数据：格式化注册资本
            if data.get("company_info", {}).get("company_capital"):
                data["company_info"]["company_capital"] = CompanyInfo.format_capital(
                    data["company_info"]["company_capital"]
                )

            return CaseData(**data)
        except Exception as e:
            print(f"加载案件数据失败: {e}")
            return None

    def delete_case(self, case_id: str) -> bool:
        """删除案件数据文件"""
        try:
            file_path = self._get_case_path(case_id)

            if file_path.exists():
                file_path.unlink()

            return True
        except Exception as e:
            print(f"删除案件数据失败: {e}")
            return False

    def list_cases(self) -> List[Dict]:
        """列出所有案件摘要"""
        cases = []

        try:
            for file_path in self.base_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 只返回摘要信息
                    cases.append({
                        "id": data.get("id", ""),
                        "target_company": data.get("company_info", {}).get("target_company", ""),
                        "legal_representative": data.get("company_info", {}).get("legal_representative", ""),
                        "principal": data.get("debt_info", {}).get("principal", ""),
                        "created_at": data.get("created_at", ""),
                        "updated_at": data.get("updated_at", ""),
                        "source_folder": data.get("source_folder", "")
                    })
                except:
                    continue
        except Exception as e:
            print(f"列出案件失败: {e}")

        # 按更新时间倒序
        cases.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return cases

    def case_exists(self, case_id: str) -> bool:
        """检查案件是否存在"""
        return self._get_case_path(case_id).exists()

    def get_case_count(self) -> int:
        """获取案件总数"""
        return len(list(self.base_dir.glob("*.json")))

    def export_to_json(self, case_data: CaseData, output_path: str = None) -> str:
        """导出案件数据为JSON文件"""
        if output_path is None:
            output_dir = self.base_dir.parent / "exports"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f"case_{case_data.id}_{timestamp}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(case_data.model_dump(), f, ensure_ascii=False, indent=2)

        return str(output_path)

    def import_from_json(self, json_path: str) -> Optional[CaseData]:
        """从JSON文件导入案件数据"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 兼容存量数据：格式化注册资本
            if data.get("company_info", {}).get("company_capital"):
                data["company_info"]["company_capital"] = CompanyInfo.format_capital(
                    data["company_info"]["company_capital"]
                )

            case_data = CaseData(**data)
            self.save_case(case_data)
            return case_data
        except Exception as e:
            print(f"导入案件数据失败: {e}")
            return None
