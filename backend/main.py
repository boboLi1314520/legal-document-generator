"""
法律文书自动生成系统 - 后端入口
支持开发环境和 Docker 容器化部署
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router

app = FastAPI(
    title="法律文书自动生成系统",
    description="基于 AI Agent 的智能法律文书生成平台",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(router, prefix="/api")


@app.get("/api/status")
async def status():
    return {"status": "ok", "service": "backend"}


# ==================== 前端静态文件服务 ====================

# 查找前端构建目录
_current_dir = os.path.dirname(os.path.abspath(__file__))
_frontend_candidates = [
    os.path.join(_current_dir, "..", "frontend", "dist"),      # Docker
    os.path.join(_current_dir, "..", "..", "frontend", "dist"), # 开发环境
]
FRONTEND_DIR = None
for _candidate in _frontend_candidates:
    _abs_path = os.path.normpath(_candidate)
    if os.path.isdir(_abs_path):
        FRONTEND_DIR = _abs_path
        break

if FRONTEND_DIR:
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {"message": "法律文书自动生成系统 API", "status": "running"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
