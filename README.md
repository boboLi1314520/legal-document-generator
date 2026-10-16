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

### macOS 一键启动

1. 双击 `启动.command`。脚本依次尝试 Python 3.14、3.13、3.12、3.11，选中第一个满足 **3.11 ≤ 版本 < 3.15** 的解释器，据此创建/复用 `.venv-mac-<版本>` 虚拟环境。
2. 首次运行会创建独立环境并安装依赖，可能需要几分钟。想安装更新版本时，可从 [Python 3.14.8 下载页](https://www.python.org/downloads/release/python-3148/) 获取 macOS 安装包。
3. 如果 macOS 提示无法验证文件，按住 Control 点击 `启动.command`，选择“打开”。
4. 浏览器会打开法律文书系统。API Key 配置在 `backend/.env`。

启动器使用**本机**已安装的最高兼容版本（例如本机装的是 Python 3.12.14，就会用 3.12 并建 `.venv-mac-3.12`）。Python 3.15 虽已发布，但当前 ONNX Runtime 尚无 Python 3.15 的 macOS ARM 安装包。

> **若本项目是从 Windows 打包（zip）传来的**，`.command` 很可能既丢了执行权限、又被 Gatekeeper 拦下。先执行：
>
> ```bash
> chmod +x *.command
> xattr -dr com.apple.quarantine .
> ```
>
> 再双击。若仍提示“无法验证”，按住 Control 点击 → 打开。
> 下次打包时用 macOS 自带的“压缩”或 `ditto -c -k --keepParent`，可以保住执行位。

#### macOS 的三个启动脚本

| 脚本 | 用途 |
|---|---|
| `启动.command` | 一键启动。跑的是 `frontend/dist` 里的**构建产物** |
| `开发模式.command` | 后端 + 前端**热更新**（改 `src/` 立即生效，无需构建），访问 http://localhost:3000 |
| `重启后端.command` | 杀掉占用 8002 的进程并重启后端 |

三者共用 `scripts/mac_common.sh`（负责找 Python、建/校验虚拟环境、按需装依赖、清理端口、探活）。端口被占用时脚本会打印占用者的 PID、启动时间与完整命令行，然后终止它——不会静默失败。

### Windows 一键启动

双击 `启动.bat`。首次运行会安装后端依赖并启动系统。开发者如需同时运行前端热更新，可双击 `启动器.bat`。

### 手动启动和前端开发

配置 `backend/.env`：

```text
DEEPSEEK_API_KEY=您的DeepSeek_API_Key
```

一键启动使用现有的 `frontend/dist`，无需安装 Node.js。**要改前端就直接双击 `开发模式.command`**（Windows 用 `启动器.bat`）——它会在后台起后端、前台起前端热更新，并自动打开浏览器。

若想手动控制，在两个终端分别运行：

```bash
# 终端 1：后端（必须 cd 到 backend，main.py 里有 `from app.api.routes import ...`）
cd backend
python3 main.py

# 终端 2：前端开发服务器
cd frontend
npm install
npm run dev
```

> 手动方式要自己保证 `python3` 能导入后端依赖。更稳妥的是用一键启动建好的虚拟环境：
> `.venv-mac-<版本>/bin/python main.py`（版本号按实际存在的目录调整，例如 `.venv-mac-3.12`）。

开发模式访问 http://localhost:3000；一键启动访问 http://127.0.0.1:8002。

> **一键启动显示的前端＝`frontend/dist/` 里的构建产物，不是 `frontend/src/` 源码。**
> 两者不会自动同步：改了 `src/` 却不重新构建，页面上永远是旧版（这是最容易踩的坑——后端不报错，页面也正常打开，只是内容是旧的）。
> 要让一键启动用上最新前端：
>
> ```bash
> cd frontend
> npm run build
> ```
>
> 构建后**无需重启后端**（它直接读取磁盘），在浏览器按 `Cmd + Shift + R` 强制刷新即可。

## 使用流程

1. **上传文件** - 上传 PDF 文件或 ZIP 压缩包
2. **查看案件** - AI 自动解析，每个 PDF 生成一个案件卡片
3. **编辑信息** - 修改/补充案件信息
4. **生成文书** - 选择文书类型，一键生成
5. **下载结果** - 下载生成的 Excel 和 Word 文件

## 系统要求

- Python 3.11 至 3.14；macOS 一键启动优先使用 Python 3.14
- Windows 10/11 或 macOS 14+（Apple Silicon）
- Node.js 18+ 仅用于前端开发
- DeepSeek API Key，用于 AI 解析和助手功能

## 技术栈

**后端**
- FastAPI - Web 框架
- LangChain - AI Agent 框架
- DeepSeek - 大语言模型
- RapidOCR + ONNX Runtime - OCR 识别
- PyMuPDF - PDF 解析
- OpenPyXL - Excel 生成
- python-docx - Word 生成

**前端**
- Vue 3 - 前端框架
- Vite - 构建工具
- Axios - HTTP 客户端

## 目录结构

```text
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
│   ├── src/                   # Vue 前端源码
│   ├── vite.config.js         # Vite 配置
│   └── dist/                  # 已构建前端
├── 启动.command                # macOS 一键启动
├── 启动.bat                    # Windows 一键启动
└── README.md                  # 说明文档
```

## 常见问题：前端构建报错

如果这个项目是从 **Windows 电脑打包（zip）后传到 Mac** 的，仓库里自带的 `node_modules` 是 Windows 版，在 Mac 上 `npm run build` 会连续报下面两种错。这不是代码问题，重装一次依赖即可。

### 1. `node_modules/.bin/vite: Permission denied`

Windows 打的 zip 会丢失 Unix 可执行位。`.bin/` 下 Windows 用的 `vite.cmd`、`vite.ps1` 是 `rwxrwxrwx`，而 Mac/Linux 用的无扩展名 shim 全是 `-rw-rw-rw-`（没有 `x`）。

```bash
cd frontend
chmod +x node_modules/.bin/*
```

### 2. `Cannot find module '@rollup/rollup-darwin-arm64'`

自带的 `node_modules` 里只有 Windows 的原生二进制（`@rollup/rollup-win32-*`、`@esbuild/win32-x64`）。`package-lock.json` 虽然记录了**全平台**条目，但安装时 npm 只装与当前平台匹配的那一份，所以搬到 Apple Silicon 上就找不到自己的二进制了。

在 `frontend` 目录重跑一次安装即可按当前平台补齐：

```bash
cd frontend
npm install
```

> **不要删 `package-lock.json`** ——全平台的条目都在里面，靠它才能准确补装缺失的那份。删掉会导致依赖被重新解析、版本漂移。

装完确认一下平台包是否到位：`ls node_modules/@rollup/` 应能看到 `rollup-darwin-arm64`。

### 附：npm 11 会拦安装脚本

`npm install` 时可能出现这样的警告：

```text
npm warn install-scripts 2 packages have install scripts not yet covered by allowScripts:
npm warn install-scripts   esbuild@0.21.5 (postinstall: node install.js)
npm warn install-scripts   fsevents@2.3.3 (install: (install scripts present))
```

**实测不批准也能正常构建**（esbuild 的二进制通过 `@esbuild/darwin-arm64` 提供，不依赖 postinstall），可以忽略。若构建确实失败，再执行 `npm install-scripts approve esbuild`。

## 注意事项

- API Key 保存在本地 `backend/.env` 文件中
- 生成的文件保存在 `backend/outputs` 目录
- 上传的 PDF 文件保存在 `backend/uploads` 目录
- macOS 后端日志保存在 `backend/server.log`
