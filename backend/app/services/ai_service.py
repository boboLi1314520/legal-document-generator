"""
LangChain AI助手后端服务 - DeepSeek版本

使用DeepSeek API（兼容OpenAI格式）
"""

import os
import json
import asyncio
from typing import List, Optional, Dict, Any, AsyncGenerator

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# LangChain imports
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# 法律助手系统提示词
LEGAL_ASSISTANT_PROMPT = """你是一个专业的法律文书助手，专门帮助用户处理法律文书相关的任务。

你的职责包括：
1. 解答法律相关问题，特别是关于公司法、合同法、诉讼程序等
2. 分析案件材料，提取关键信息
3. 协助填写法律表单，确保信息准确完整
4. 解释法律文书条款和含义
5. 提供诉讼建议和风险评估

当前案件信息：
{context}

请根据用户的问题提供专业、准确的回答。如果涉及法律建议，请说明这是一般性建议，建议咨询专业律师。
回答时请使用简洁清晰的中文，必要时可以使用列表或分段来组织内容。"""


def get_llm():
    """获取DeepSeek LLM实例"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("未找到DEEPSEEK_API_KEY环境变量，请在.env文件中配置")

    # DeepSeek兼容OpenAI API格式
    return ChatOpenAI(
        model="deepseek-chat",  # DeepSeek模型名称
        openai_api_key=api_key,
        openai_api_base="https://api.deepseek.com/v1",  # DeepSeek API地址
        temperature=0.7,
        streaming=True
    )


def build_context_string(context: Optional[Dict[str, Any]]) -> str:
    """将上下文数据转换为字符串"""
    if not context:
        return "暂无案件信息"

    parts = []

    # 公司信息
    if context.get("company_info"):
        company = context["company_info"]
        parts.append(f"""公司信息：
- 企业名称：{company.get('target_company', '未知')}
- 法定代表人：{company.get('legal_representative', '未知')}
- 注册资本：{company.get('company_capital', '未知')}
- 住所：{company.get('company_addr', '未知')}
- 成立日期：{company.get('company_establish', '未知')}
- 注销日期：{company.get('company_cancel_apply', '未知')}""")

    # 被告信息
    if context.get("defendants"):
        defendants_text = "\n".join([
            f"  {i+1}. {d.get('def_name', '未知')}（{d.get('is_legal_rep', False) and '法定代表人' or '股东'}）- 身份证：{d.get('def_id', '未知')}，持股：{d.get('def_share', '未知')}"
            for i, d in enumerate(context["defendants"])
        ])
        parts.append(f"被告/股东信息：\n{defendants_text}")

    # 债务信息
    if context.get("debt_info"):
        debt = context["debt_info"]
        parts.append(f"""债务信息：
- 贷款本金合计：{debt.get('loan_total', '未知')} 元
- 欠付本金：{debt.get('principal', '未知')} 元
- 利息：{debt.get('interest', '未知')} 元
- 罚息：{debt.get('penalty_cutoff', '未知')} 元
- 保全金额：{debt.get('guarantee_amount', '未知')} 元""")

    # 合同信息
    if context.get("loan_contracts"):
        loan = context["loan_contracts"]
        parts.append(f"""合同信息：
- 额度合同数：{loan.get('quota_count', 0)}
- 借款合同数：{loan.get('loan_count', 0)}""")

    return "\n\n".join(parts) if parts else "暂无案件信息"


async def stream_chat_response(
    message: str,
    history: List[Dict] = [],
    context: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[str, None]:
    """流式对话响应"""

    llm = get_llm()

    # 构建消息列表
    messages = []

    # 添加系统提示
    context_str = build_context_string(context)
    messages.append(SystemMessage(content=LEGAL_ASSISTANT_PROMPT.format(context=context_str)))

    # 添加历史消息
    for msg in history:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg.get("content", "")))
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg.get("content", "")))

    # 添加当前用户消息
    messages.append(HumanMessage(content=message))

    # 流式生成响应
    try:
        async for chunk in llm.astream(messages):
            content = chunk.content
            if content:
                yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"


async def chat_response(
    message: str,
    history: List[Dict] = [],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """非流式对话响应"""

    llm = get_llm()

    # 构建消息列表
    messages = []

    # 添加系统提示
    context_str = build_context_string(context)
    messages.append(SystemMessage(content=LEGAL_ASSISTANT_PROMPT.format(context=context_str)))

    # 添加历史消息
    for msg in history:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg.get("content", "")))
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg.get("content", "")))

    # 添加当前用户消息
    messages.append(HumanMessage(content=message))

    # 调用LLM
    response = await llm.ainvoke(messages)

    return response.content


async def analyze_file_content(
    file_content: str,
    question: Optional[str] = None
) -> str:
    """分析文件内容"""

    llm = get_llm()

    prompt = f"""请分析以下文件内容，并回答用户的问题。

文件内容：
{file_content[:3000]}  # 限制长度避免token过多

用户问题：{question or "请总结这个文件的主要内容，并提取关键信息"}

请用专业的法律角度分析，给出结构化的回答，包括：
1. 文件类型和用途
2. 关键信息提取
3. 法律要点分析
"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return response.content


async def get_form_field_suggestion(
    field_name: str,
    field_label: str,
    case_data: Optional[Dict[str, Any]] = None,
    current_value: Optional[str] = None
) -> str:
    """获取表单字段填充建议"""

    llm = get_llm()

    context_str = build_context_string(case_data) if case_data else "暂无案件信息"

    prompt = f"""基于以下案件信息，为表单字段提供填充建议。

案件信息：
{context_str}

字段名称：{field_name}
字段标签：{field_label}
当前值：{current_value or "无"}

请给出：
1. 建议填充值
2. 建议理由
3. 注意事项

请简洁回答，直接给出建议值和简要说明。"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return response.content


async def check_form_completeness(case_data: Dict[str, Any]) -> str:
    """检查表单完整性"""

    llm = get_llm()

    prompt = f"""请检查以下案件数据的完整性和正确性：

{json.dumps(case_data, ensure_ascii=False, indent=2)}

请检查：
1. 必填字段是否完整（公司名称、法定代表人、被告信息、债务金额等）
2. 数据格式是否正确（身份证号、金额、日期等）
3. 逻辑是否合理（金额计算、日期先后等）
4. 给出改进建议

请用结构化的方式列出检查结果。"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return response.content
