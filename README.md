# 法律文书自动生成系统

基于 AI Agent 的智能法律文书生成平台

## 功能特性

- 📄 支持批量上传 PDF 文件
- 📦 支持 ZIP 压缩包（内含多个 PDF）
- 🤖 AI 自动解析提取案件信息
- 📊 自动生成要素 Excel
- 📝 批量生成法律文书（起诉状、证据目录、申请书等）
- 🎨 简洁美观的 Web 界面

## 快速开始

### 方式一：一键启动（推荐）

1. 双击运行 `启动器.bat`
2. 首次运行会提示配置 API Key
3. 自动安装依赖并启动服务
4. 浏览器自动打开前端界面

### 方式二：手动启动

**1. 配置 API Key**

编辑 `backend/.env` 文件：
```
DEEPSEEK_API_KEY=您的DeepSeek_API_Key
```

获取 API Key: https://platform.deepseek.com

**2. 安装后端依赖**

```bash
cd backend
pip install -r requirements.txt
```

**3. 安装前端依赖**

```bash
cd frontend
npm install
```

**4. 启动服务**

```bash
# 终端1：启动后端
cd backend
python main.py

# 终端2：启动前端
cd frontend
npm run dev
```

**5. 访问**

打开浏览器访问: http://localhost:3000

## 使用流程

1. **上传文件** - 上传 PDF 文件或 ZIP 压缩包
2. **查看案件** - AI 自动解析，每个 PDF 生成一个案件卡片
3. **编辑信息** - 修改/补充案件信息
4. **生成文书** - 选择文书类型，一键生成
5. **下载结果** - 下载生成的 Excel 和 Word 文件

## 系统要求

- Python 3.8+
- Node.js 18+
- Windows 7/8/10/11

## 技术栈

**后端**
- FastAPI - Web 框架
- LangChain - AI Agent 框架
- DeepSeek - 大语言模型
- PyMuPDF - PDF 解析
- OpenPyXL - Excel 生成
- python-docx - Word 生成

**前端**
- Vue 3 - 前端框架
- Vite - 构建工具
- Axios - HTTP 客户端

## 目录结构

```
项目/
├── backend/
│   ├── app/
│   │   ├── api/routes.py      # API 路由
│   │   ├── core/agent.py      # AI Agent
│   │   └── services/          # 服务模块
│   ├── main.py                # 入口文件
│   ├── requirements.txt       # Python 依赖
│   └── .env                   # 环境配置
├── frontend/
│   ├── src/
│   │   ├── App.vue            # 主组件
│   │   └── api.js             # API 调用
│   ├── vite.config.js         # Vite 配置
│   └── package.json           # Node 依赖
├── 启动器.bat                  # 一键启动脚本
└── README.md                  # 说明文档
```

## 注意事项

- API Key 仅存储在本地 .env 文件中，不会上传
- 生成的文件保存在 backend/outputs 目录
- 上传的 PDF 文件保存在 backend/uploads 目录
