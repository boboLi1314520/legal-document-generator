"""
LangChain AI助手后端服务示例

这个模块展示了如何使用LangChain搭建AI助手后端服务。
支持流式响应、上下文注入、文件分析等功能。

依赖安装:
pip install langchain langchain-openai langchain-community fastapi uvicorn python-multipart

使用方法:
1. 设置环境变量 OPENAI_API_KEY 或使用其他LLM提供商
2. 运行: uvicorn ai_service:app --reload --port 8001
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, AsyncGenerator
import json
import asyncio
import os

# LangChain imports
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

app = FastAPI(title="AI Legal Assistant Service")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== 请求模型 ==============

class ChatMessage(BaseModel):
    role: str
    content: str
    time: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    context: Optional[Dict[str, Any]] = None
    case_id: Optional[str] = None
    stream: bool = True

class FileAnalyzeRequest(BaseModel):
    file_id: str
    question: Optional[str] = None

class FormSuggestionRequest(BaseModel):
    case_id: str
    field_name: str
    current_value: Optional[str] = None

# ============== LangChain配置 ==============

def get_llm():
    """获取LLM实例，支持多种提供商"""
    # 方式1: 使用OpenAI
    if os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            streaming=True
        )

    # 方式2: 使用本地Ollama
    # 需要先运行: ollama serve
    return ChatOllama(
        model="qwen2.5:7b",  # 或其他本地模型
        temperature=0.7
    )

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
"""

def build_context_string(context: Optional[Dict[str, Any]]) -> str:
    """将上下文数据转换为字符串"""
    if not context:
        return "暂无案件信息"

    parts = []

    # 公司信息
    if context.get("company_info"):
        company = context["company_info"]
        parts.append(f"""
公司信息：
- 企业名称：{company.get('target_company', '未知')}
- 法定代表人：{company.get('legal_representative', '未知')}
- 注册资本：{company.get('company_capital', '未知')}
- 住所：{company.get('company_addr', '未知')}
""")

    # 被告信息
    if context.get("defendants"):
        defendants_text = "\n".join([
            f"- {d.get('def_name', '未知')}（{d.get('is_legal_rep', False) and '法定代表人' or '股东'}）：身份证 {d.get('def_id', '未知')}"
            for d in context["defendants"]
        ])
        parts.append(f"被告/股东信息：\n{defendants_text}")

    # 债务信息
    if context.get("debt_info"):
        debt = context["debt_info"]
        parts.append(f"""
债务信息：
- 欠付本金：{debt.get('principal', '未知')} 元
- 利息：{debt.get('interest', '未知')} 元
- 罚息：{debt.get('penalty_cutoff', '未知')} 元
- 保全金额：{debt.get('guarantee_amount', '未知')} 元
""")

    return "\n".join(parts) if parts else "暂无案件信息"

# ============== API端点 ==============

@app.post("/api/ai/chat")
async def chat(request: ChatRequest):
    """AI对话接口，支持流式和非流式响应"""

    if request.stream:
        return StreamingResponse(
            stream_chat(request),
            media_type="text/event-stream"
        )
    else:
        return await simple_chat(request)

async def stream_chat(request: ChatRequest) -> AsyncGenerator[str, None]:
    """流式对话响应"""

    try:
        llm = get_llm()

        # 构建消息历史
        messages = []

        # 添加系统提示
        context_str = build_context_string(request.context)
        messages.append(SystemMessage(content=LEGAL_ASSISTANT_PROMPT.format(context=context_str)))

        # 添加历史消息
        for msg in request.history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))

        # 添加当前用户消息
        messages.append(HumanMessage(content=request.message))

        # 流式生成响应
        async for chunk in llm.astream(messages):
            content = chunk.content
            if content:
                yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

async def simple_chat(request: ChatRequest) -> Dict[str, Any]:
    """非流式对话响应"""

    try:
        llm = get_llm()

        # 构建消息历史
        messages = []

        # 添加系统提示
        context_str = build_context_string(request.context)
        messages.append(SystemMessage(content=LEGAL_ASSISTANT_PROMPT.format(context=context_str)))

        # 添加历史消息
        for msg in request.history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))

        # 添加当前用户消息
        messages.append(HumanMessage(content=request.message))

        # 调用LLM
        response = await llm.ainvoke(messages)

        return {
            "success": True,
            "message": response.content
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/ai/analyze-file")
async def analyze_file(request: FileAnalyzeRequest):
    """分析文件内容"""

    try:
        llm = get_llm()

        # 这里应该从数据库或文件系统读取文件内容
        # 示例中使用模拟数据
        file_content = "这是从文件中提取的内容..."  # 实际应该读取文件

        prompt = f"""请分析以下文件内容，并回答用户的问题。

文件内容：
{file_content}

用户问题：{request.question or "请总结这个文件的主要内容"}

请用专业的法律角度分析，并给出结构化的回答。
"""

        response = await llm.ainvoke([HumanMessage(content=prompt)])

        return {
            "success": True,
            "analysis": response.content
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/ai/form-suggestions")
async def get_form_suggestions(request: FormSuggestionRequest):
    """获取表单字段填充建议"""

    try:
        llm = get_llm()

        # 这里应该获取案件数据
        # 示例中使用模拟数据
        case_data = {}  # 实际应该从数据库读取

        prompt = f"""基于以下案件信息，为表单字段 "{request.field_name}" 提供填充建议。

案件信息：{json.dumps(case_data, ensure_ascii=False)}

当前值：{request.current_value or "无"}

请给出：
1. 建议值
2. 建议理由
3. 注意事项
"""

        response = await llm.ainvoke([HumanMessage(content=prompt)])

        return {
            "success": True,
            "suggestion": response.content
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/ai/check-form")
async def check_form_completeness(case_id: str):
    """检查表单完整性"""

    try:
        llm = get_llm()

        # 获取案件数据
        case_data = {}  # 实际应该从数据库读取

        prompt = f"""请检查以下案件数据的完整性和正确性：

{json.dumps(case_data, ensure_ascii=False, indent=2)}

请：
1. 列出缺失的必填字段
2. 标记可能存在问题的数据
3. 给出改进建议
"""

        response = await llm.ainvoke([HumanMessage(content=prompt)])

        return {
            "success": True,
            "check_result": response.content
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ============== 使用LangChain Chain的高级示例 ==============

class LegalAssistantChain:
    """使用LangChain Chain构建的法律助手"""

    def __init__(self):
        self.llm = get_llm()
        self.memory = ConversationBufferMemory(return_messages=True)

        # 创建提示模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", LEGAL_ASSISTANT_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

        # 创建链
        self.chain = self.prompt | self.llm | StrOutputParser()

    async def chat(self, user_input: str, context: str) -> str:
        """执行对话"""
        response = await self.chain.ainvoke({
            "input": user_input,
            "history": self.memory.chat_memory.messages,
            "context": context
        })

        # 保存到记忆
        self.memory.chat_memory.add_user_message(user_input)
        self.memory.chat_memory.add_ai_message(response)

        return response

# 全局实例
legal_assistant = LegalAssistantChain()

@app.post("/api/ai/chat-advanced")
async def chat_advanced(request: ChatRequest):
    """使用Chain的高级对话接口"""

    try:
        context_str = build_context_string(request.context)
        response = await legal_assistant.chat(request.message, context_str)

        return {
            "success": True,
            "message": response
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ============== RAG示例（检索增强生成）=============

# 注意：需要安装额外的向量数据库依赖
# pip install langchain-chroma chromadb

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

class LegalRAGAssistant:
    """基于RAG的法律助手，可以检索法律文档"""

    def __init__(self, docs_path: str = "./legal_docs"):
        self.llm = get_llm()
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = None
        self.docs_path = docs_path

        # 初始化向量存储
        self._init_vectorstore()

    def _init_vectorstore(self):
        """初始化向量存储"""
        if not os.path.exists(self.docs_path):
            os.makedirs(self.docs_path)
            return

        documents = []

        # 加载所有法律文档
        for file in os.listdir(self.docs_path):
            file_path = os.path.join(self.docs_path, file)
            if file.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            elif file.endswith('.txt'):
                loader = TextLoader(file_path)
                documents.extend(loader.load())

        if documents:
            # 分割文档
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(documents)

            # 创建向量存储
            self.vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings
            )

    async def query(self, question: str) -> str:
        """查询法律文档"""
        if not self.vectorstore:
            return "法律文档库暂未初始化"

        # 检索相关文档
        docs = self.vectorstore.similarity_search(question, k=3)

        # 构建上下文
        context = "\n\n".join([doc.page_content for doc in docs])

        # 生成回答
        prompt = f"""基于以下法律文档内容回答问题：

{context}

问题：{question}

请给出专业的法律解答，并注明参考的法律条款。
"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content

# ============== 健康检查 ==============

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "AI Legal Assistant"}

# ============== 主函数 ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
