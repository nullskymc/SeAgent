import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

import uvicorn

from database.db import db
from database.models import MODELS
from routes import api_router

# 初始化 FastAPI 应用
app = FastAPI(
    title="SeAgent API",
    description="语义代理API服务",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允许所有来源，生产环境中应配置为特定来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化日志配置
logging.basicConfig(level=logging.INFO)

# 注册API路由
# 所有的API路由都应该以 /api 开头，以区别于前端路由
app.include_router(api_router, prefix="/api")

# 挂载静态文件 - 这是处理前端应用的核心
# 确保这个挂载点在所有其他路由之后
dist_dir = os.path.join("seagent_vue", "dist")
if os.path.exists(dist_dir):
    # 创建一个自定义的静态文件处理类，确保所有前端路由都能正确返回index.html
    class CustomStaticFiles(StaticFiles):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
        async def get_response(self, path: str, scope):
            try:
                response = await super().get_response(path, scope)
                return response
            except HTTPException as ex:
                if ex.status_code == 404:
                    # 对于404错误，返回index.html以支持前端路由
                    response = await super().get_response("index.html", scope)
                    return response
                raise ex
    
    app.mount("/", CustomStaticFiles(directory=dist_dir, html=True), name="static")
else:
    logging.warning("Frontend build directory not found. Please run 'npm run build' in the seagent_vue directory.")

# 数据库初始化
@app.on_event("startup")
def on_startup():
    logging.info("Connecting to database...")
    if not db.is_closed():
        db.close()
    db.connect()
    logging.info("Creating tables...")
    db.create_tables(MODELS)
    logging.info("Tables created successfully.")
    db.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)