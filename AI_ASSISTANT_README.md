# AI法律助手 - 集成指南

## 前端组件

已在 `frontend/src/components/AIAssistant.vue` 创建了完整的AI助手聊天组件。

### 功能特性

- ✅ 智能问答对话（支持流式响应）
- ✅ 文件内容分析
- ✅ 法律文书解释
- ✅ 表单辅助填写建议
- ✅ 多轮对话记忆
- ✅ 快捷问题模板
- ✅ 上下文感知（根据当前案件信息回答）

### 使用方式

组件已自动集成到主界面，右下角显示浮动按钮，点击即可打开聊天窗口。

```vue
<AIAssistant :context-data="caseData" :case-id="caseData.id" />
```

## 后端服务

### 方式一：独立运行AI服务

```bash
# 安装依赖
cd backend
pip install -r requirements-ai.txt

# 设置OpenAI API Key（或使用其他提供商）
export OPENAI_API_KEY=your-api-key

# 运行服务
uvicorn ai_service:app --reload --port 8001
```

### 方式二：集成到现有后端

将 `ai_service.py` 中的路由和函数复制到您的主后端文件中。

### 方式三：使用本地模型（Ollama）

```bash
# 安装Ollama
# 访问 https://ollama.ai 下载安装

# 拉取中文模型
ollama pull qwen2.5:7b

# 运行Ollama服务
ollama serve
```

修改 `ai_service.py` 中的 `get_llm()` 函数：

```python
def get_llm():
    return ChatOllama(
        model="qwen2.5:7b",
        temperature=0.7
    )
```

## API接口

### 1. 对话接口

```
POST /api/ai/chat
```

请求体：
```json
{
  "message": "请分析当前案件的法律要点",
  "history": [
    {"role": "user", "content": "之前的问题"},
    {"role": "assistant", "content": "之前的回答"}
  ],
  "context": {
    "company_info": {...},
    "defendants": [...],
    "debt_info": {...}
  },
  "case_id": "case-123",
  "stream": true
}
```

### 2. 文件分析

```
POST /api/ai/analyze-file
```

请求体：
```json
{
  "file_id": "file-123",
  "question": "这个文件的主要内容是什么？"
}
```

### 3. 表单建议

```
POST /api/ai/form-suggestions
```

请求体：
```json
{
  "case_id": "case-123",
  "field_name": "legal_representative",
  "current_value": ""
}
```

## 高级功能

### RAG（检索增强生成）

将法律文档放入 `./legal_docs/` 目录，系统会自动：
1. 加载并分割文档
2. 创建向量索引
3. 根据问题检索相关条款
4. 生成基于法律条款的回答

```python
from ai_service import LegalRAGAssistant

rag = LegalRAGAssistant("./legal_docs")
answer = await rag.query("公司法关于股东责任的规定是什么？")
```

### 自定义提示词

修改 `LEGAL_ASSISTANT_PROMPT` 来自定义AI助手的角色和行为：

```python
LEGAL_ASSISTANT_PROMPT = """你是一个专业的法律文书助手...
（添加更多指令）
"""
```

## 部署建议

### 生产环境配置

1. **API Key安全**：使用环境变量或密钥管理服务
2. **请求限流**：添加速率限制防止滥用
3. **日志记录**：记录对话日志用于审计
4. **缓存优化**：对常见问题使用缓存

### 示例Nginx配置

```nginx
location /api/ai/ {
    proxy_pass http://localhost:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_cache_bypass $http_upgrade;
    proxy_buffering off;  # 支持流式响应
}
```

## 常见问题

**Q: 如何切换不同的LLM提供商？**
A: 修改 `get_llm()` 函数，返回对应的LangChain模型实例。

**Q: 如何支持更多文件类型？**
A: 安装对应的loader，如 `langchain-docx` 支持Word文档。

**Q: 如何提高回答质量？**
A: 1) 优化提示词 2) 使用RAG添加专业知识库 3) 选择更强的模型

## 文件结构

```
frontend/
  src/
    components/
      AIAssistant.vue    # AI助手组件
    api.js               # API调用方法（已添加AI相关API）
    App.vue              # 主应用（已集成AI助手）

backend/
  ai_service.py          # LangChain后端服务
  requirements-ai.txt    # Python依赖
```
