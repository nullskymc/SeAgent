from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
import os
import shutil
import uuid
from typing import List, Optional
import logging

from routes.auth import get_current_user
from utils.vectorstore import create_vector_db, merge_collections
from utils.loader import text_loader, pdf_loader, csv_loader
from database.models.user import User

router = APIRouter()

# 允许的文件类型及其对应的加载器
file_loaders = {
    "txt": text_loader,
    "pdf": pdf_loader,
    "csv": csv_loader
}

# 临时文件存储路径
TEMP_UPLOAD_DIR = "temp_uploads"
# 确保临时目录存在
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# 知识库存储基础路径
KNOWLEDGE_BASE_DIR = "vector_db"
os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)

@router.post("/upload")
async def upload_knowledge_file(
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件到知识库
    - file: 要上传的文件
    - collection_name: 知识库集合名称
    """
    try:
        # 检查文件类型
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in file_loaders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(file_loaders.keys())}"
            )
        
        # 用户特定的知识库路径
        user_kb_dir = os.path.join(KNOWLEDGE_BASE_DIR, f"user_{current_user.id}")
        os.makedirs(user_kb_dir, exist_ok=True)
        
        # 保存临时文件
        temp_file_path = os.path.join(TEMP_UPLOAD_DIR, f"{uuid.uuid4()}.{file_ext}")
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 确定存储路径和集合名称
        db_path = os.path.join(user_kb_dir, collection_name)
        
        # 检查是否已存在该集合
        if os.path.exists(db_path):
            # 如果存在，合并新数据
            merge_collections(
                base_db_path=db_path,
                new_data_path=temp_file_path,
                loader=file_loaders[file_ext],
                collection_name=collection_name
            )
            message = f"文件 {file.filename} 已成功合并到知识库 {collection_name}"
        else:
            # 创建新的知识库
            create_vector_db(
                data_path=temp_file_path,
                db_path=db_path,
                loader=file_loaders[file_ext],
                collection_name=collection_name
            )
            message = f"文件 {file.filename} 已成功上传到新知识库 {collection_name}"
        
        # 清理临时文件
        os.remove(temp_file_path)
        
        return {"status": "success", "message": message}
    
    except Exception as e:
        # 确保清理临时文件
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        logging.error(f"知识库上传失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败: {str(e)}"
        )

@router.get("/collections")
async def get_knowledge_collections(current_user: User = Depends(get_current_user)):
    """获取当前用户的所有知识库集合"""
    try:
        # 用户特定的知识库路径
        user_kb_dir = os.path.join(KNOWLEDGE_BASE_DIR, f"user_{current_user.id}")
        
        if not os.path.exists(user_kb_dir):
            return {"collections": []}
        
        # 获取所有子目录，每个子目录是一个集合
        collections = [d for d in os.listdir(user_kb_dir) 
                      if os.path.isdir(os.path.join(user_kb_dir, d))]
        
        return {"collections": collections}
    
    except Exception as e:
        logging.error(f"获取知识库集合失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取知识库集合失败: {str(e)}"
        )

@router.delete("/collections/{collection_name}")
async def delete_knowledge_collection(
    collection_name: str,
    current_user: User = Depends(get_current_user)
):
    """删除特定的知识库集合"""
    try:
        # 用户特定的知识库路径
        user_kb_dir = os.path.join(KNOWLEDGE_BASE_DIR, f"user_{current_user.id}")
        collection_path = os.path.join(user_kb_dir, collection_name)
        
        # 检查集合是否存在
        if not os.path.exists(collection_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"知识库集合 {collection_name} 不存在"
            )
        
        # 删除集合目录
        shutil.rmtree(collection_path)
        
        return {"status": "success", "message": f"知识库集合 {collection_name} 已成功删除"}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"删除知识库集合失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除知识库集合失败: {str(e)}"
        )