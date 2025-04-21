# 第一阶段：构建 Python 依赖
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 文件并安装 Python 依赖
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 第二阶段：最终运行环境
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 从第一阶段复制已安装的 Python 依赖
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制所有文件到容器中
COPY . /app

# 复制本地构建好的 Vue 网站静态文件到镜像中
COPY ./seagent_vue/dist /app/seagent_vue/dist

# 暴露端口 8000
EXPOSE 8000

# 启动应用
CMD ["uvicorn", "fast_app:app", "--host", "0.0.0.0", "--port", "8000"]
