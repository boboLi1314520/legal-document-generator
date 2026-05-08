"""
法律文书自动生成系统 - 后端入口
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# 注册路由
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "法律文书自动生成系统 API", "status": "running"}


@app.get("/api/status")
async def status():
    return {"status": "ok", "service": "backend"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
