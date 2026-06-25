"""
法律文书自动生成系统 - 一键启动脚本（方案1：预构建便携包）
仅需 Python 3.8+，无需 Node.js
"""
import os
import sys
import time
import socket
import subprocess
import webbrowser
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = PROJECT_DIR / "backend"
DIST_DIR = PROJECT_DIR / "frontend" / "dist"
REQUIREMENTS = BACKEND_DIR / "requirements.txt"
ENV_FILE = BACKEND_DIR / ".env"
HOST = "127.0.0.1"
PORT = 8002
URL = f"http://{HOST}:{PORT}"

# 最小 Python 版本
MIN_PYTHON = (3, 8)


def print_banner():
    print()
    print("=" * 50)
    print("    法律文书自动生成系统  v1.0")
    print("    预构建便携版 - 仅需 Python 3.8+")
    print("=" * 50)
    print()


def check_python():
    """检查 Python 版本"""
    ver = sys.version_info[:2]
    if ver < MIN_PYTHON:
        print(f"[错误] Python 版本过低：{ver[0]}.{ver[1]}")
        print(f"        需要 Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+")
        print("        下载地址: https://www.python.org/downloads/")
        return False
    print(f"[1/5] Python {ver[0]}.{ver[1]} 环境已就绪")
    return True


def check_frontend_dist():
    """检查前端构建文件是否存在"""
    dist_index = DIST_DIR / "index.html"
    if not dist_index.exists():
        print()
        print("[错误] 未找到前端构建文件 frontend/dist/")
        print()
        print("请在已安装 Node.js 的电脑上执行以下命令：")
        print("  cd frontend")
        print("  npm install")
        print("  npm run build")
        print()
        print("然后将 frontend/dist/ 文件夹一同复制到目标电脑。")
        return False
    print(f"[2/5] 前端构建文件已就绪")
    return True


def install_dependencies():
    """检查并安装后端依赖"""
    print(f"[3/5] 检查后端依赖...")

    # 快速检查核心依赖是否已安装
    try:
        import fastapi, uvicorn, docx, openpyxl, pandas, httpx  # noqa
        print("       依赖已就绪")
        return True
    except ImportError:
        pass

    print("       首次运行，正在安装依赖（可能需要几分钟）...")
    print()

    # 尝试使用清华镜像源
    print("       [1/2] 尝试清华镜像源...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS),
         "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
        cwd=str(BACKEND_DIR),
        capture_output=False
    )

    if result.returncode != 0:
        print()
        print("       [2/2] 镜像源失败，使用默认源...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)],
            cwd=str(BACKEND_DIR),
            capture_output=False
        )

    if result.returncode != 0:
        print()
        print("[错误] 依赖安装失败，请检查网络连接后重试")
        return False

    print()
    print("       依赖安装完成！")
    return True


def configure_env():
    """检查/创建 .env 配置文件"""
    print(f"[4/5] 配置检查...")

    if ENV_FILE.exists():
        # 检查是否有有效的 API Key
        content = ENV_FILE.read_text(encoding="utf-8", errors="ignore")
        if "DEEPSEEK_API_KEY=" in content:
            key_value = content.split("DEEPSEEK_API_KEY=", 1)[1].split("\n")[0].strip()
            if key_value and key_value != "请在此输入您的APIKey" and key_value != "您的key":
                print("       配置文件已存在")
                return True

    print()
    print("       " + "-" * 55)
    print("       首次运行，需要配置 DeepSeek API Key")
    print("       如果没有 API Key，请前往 https://platform.deepseek.com 注册获取")
    print("       " + "-" * 55)
    print()

    try:
        api_key = input("请输入 DeepSeek API Key: ").strip()
    except (EOFError, KeyboardInterrupt):
        api_key = ""

    if api_key:
        ENV_FILE.write_text(f"DEEPSEEK_API_KEY={api_key}\n", encoding="utf-8")
        print("       API Key 已保存")
    else:
        ENV_FILE.write_text("DEEPSEEK_API_KEY=请在此输入您的APIKey\n", encoding="utf-8")
        print("[警告] 未输入 API Key，请稍后编辑 backend\\.env 文件")

    return True


def create_runtime_dirs():
    """创建运行时目录"""
    (BACKEND_DIR / "outputs" / "cases").mkdir(parents=True, exist_ok=True)
    (BACKEND_DIR / "uploads").mkdir(parents=True, exist_ok=True)


def check_port():
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((HOST, PORT))
        sock.close()
        return True  # 端口可用
    except OSError:
        sock.close()
        print(f"[警告] 端口 {PORT} 已被占用，将尝试终止已有进程...")
        return False


def wait_for_server(max_wait=30):
    """轮询等待服务就绪"""
    import urllib.request
    print("       等待服务就绪...", end="", flush=True)

    for i in range(max_wait // 2):
        try:
            req = urllib.request.Request(f"{URL}/api/status")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    print()
                    print("       服务已就绪！")
                    return True
        except Exception:
            pass
        time.sleep(2)
        print(".", end="", flush=True)

    print()
    print("[警告] 服务启动较慢，请稍后手动刷新浏览器")
    return False


def main():
    print_banner()

    if not check_python():
        input("\n按回车键退出...")
        sys.exit(1)

    print()
    if not check_frontend_dist():
        input("\n按回车键退出...")
        sys.exit(1)

    print()
    if not install_dependencies():
        input("\n按回车键退出...")
        sys.exit(1)

    print()
    if not configure_env():
        input("\n按回车键退出...")
        sys.exit(1)

    create_runtime_dirs()

    # 检查端口
    print()
    print(f"[5/5] 启动服务（端口 {PORT}）...")
    print()

    # 后台启动 FastAPI 服务
    server_cmd = [sys.executable, str(BACKEND_DIR / "main.py")]
    if sys.platform == "win32":
        # Windows: 使用 CREATE_NEW_CONSOLE 在新窗口启动
        subprocess.Popen(
            server_cmd,
            cwd=str(BACKEND_DIR),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        subprocess.Popen(
            server_cmd,
            cwd=str(BACKEND_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    print("=" * 50)
    print("    正在启动后端服务...")
    print("=" * 50)
    print()

    # 等待服务就绪
    wait_for_server()

    # 打开浏览器
    print(f"\n       正在打开浏览器: {URL}")
    webbrowser.open(URL)

    print()
    print("=" * 50)
    print("    启动完成！")
    print("=" * 50)
    print()
    print(f"   访问地址: {URL}")
    print()
    print("   关闭后端服务窗口即可停止服务")
    print("   如要在开发模式下修改前端，请使用 启动器.bat")
    print("=" * 50)

    # 保持运行（Windows 下等待用户输入，否则窗口会闪退）
    try:
        input("\n按回车键退出启动器（不会停止后端服务）...")
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
