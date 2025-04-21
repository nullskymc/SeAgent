import logging
import os

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.staticfiles import StaticFiles

import uvicorn

from database.db import db
from database.models import MODELS
from routes import api_router

app = FastAPI(
    title="SeAgent API",
    description="语义代理API服务",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化日志配置
logging.basicConfig(level=logging.INFO)

# 定义函数返回index.html内容
def get_index_html():
    html_path = os.path.join("seagent_vue", "dist", "index.html")
    if not os.path.exists(html_path):
        return HTMLResponse(content="<h1>前端未构建</h1><p>请在seagent_vue目录运行'npm run build'。</p>", status_code=200)
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

# 检查前端构建文件是否存在
dist_dir = os.path.join("seagent_vue", "dist")
if not os.path.exists(dist_dir):
    logging.warning("前端构建文件不存在，请在seagent_vue目录运行'npm run build'")
else:
    # 挂载静态文件 - 先挂载静态资源，但确保不会与API或路由冲突
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")
    # 恢复/static挂载，确保静态资源可以正确加载
    app.mount("/static", StaticFiles(directory=dist_dir), name="static")

# 注册API路由
app.include_router(api_router)

# 根路径 - 返回前端应用
@app.get("/")
def main():
    return get_index_html()

# 前端路由 - 返回index.html让Vue路由处理
@app.get("/login")
@app.get("/main")
@app.get("/knowledge")
def frontend_routes():
    return get_index_html()

# 通配符路由 - 处理所有其他请求
@app.get("/{path:path}")
async def catch_all(path: str, request: Request):
    # 跳过API路径，因为这些应该由API路由处理
    if path.startswith("api/") or path.startswith("auth/") or path.startswith("messages/") or path.startswith("knowledge/"):
        raise HTTPException(status_code=404, detail="API路径不存在")
    
    # 跳过静态资源路径，因为这些应该由静态文件挂载处理
    if path.startswith("assets/") or path.startswith("static/"):
        raise HTTPException(status_code=404, detail="资源文件不存在")
    
    # 对于所有其他路径，返回Vue应用
    return get_index_html()

# 数据库初始化
@app.on_event("startup")
def on_startup():
    logging.info("连接到数据库...")
    if not db.is_closed():
        db.close()
    db.connect()
    logging.info("创建表...")
    db.create_tables(MODELS)
    logging.info("表创建成功.")
    db.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)