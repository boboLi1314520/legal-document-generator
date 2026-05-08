"""
被告信息模型
"""
from pydantic import BaseModel
from typing import Optional


class DefendantInfo(BaseModel):
    """被告/股东信息"""
    def_name: Optional[str] = ""      # 姓名
    def_gender: Optional[str] = ""    # 性别
    def_nation: Optional[str] = ""    # 民族
    def_id: Optional[str] = ""        # 身份证号码
    def_addr: Optional[str] = ""      # 住址
    def_tel: Optional[str] = ""       # 电话
    def_share: Optional[str] = ""     # 持股比例
    is_legal_rep: bool = False        # 是否为法定代表人

    class Config:
        json_schema_extra = {
            "example": {
                "def_name": "陈荣",
                "def_gender": "男",
                "def_nation": "汉",
                "def_id": "32102819640124281X",
                "def_addr": "江苏省南京市玄武区XX路XX号",
                "def_tel": "13787064688",
                "def_share": "60%",
                "is_legal_rep": True
            }
        }
