FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装后端依赖
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# 复制后端代码
COPY backend/ /app/backend/

# 复制前端构建产物
COPY frontend/dist/ /app/frontend/dist/

# 复制文书模板
COPY 诉讼文书模板/ /app/诉讼文书模板/

# 创建运行时目录
RUN mkdir -p /app/backend/outputs /app/backend/uploads /app/backend/outputs/cases

# 暴露端口
EXPOSE 8002

# 启动
CMD ["python", "-u", "/app/backend/main.py"]
