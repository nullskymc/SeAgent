import logging
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import ValidationError
from typing import List, Optional
from datetime import datetime

from database.models.mcp import McpTool, McpToolCreate, McpToolUpdate, McpToolResponse
from database.models.user import User
from routes.auth import get_current_user

router = APIRouter()

@router.post("/mcp/tools", response_model=McpToolResponse)
async def create_mcp_tool(
    user_id: int = Form(...),
    name: str = Form(...),
    config: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """创建新的MCP工具"""
    try:
        # 验证用户权限
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="没有权限创建此用户的MCP工具")

        # 解析JSON配置
        try:
            config_data = json.loads(config)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"无效的JSON格式: {str(e)}")

        # 验证MCP配置格式
        if not isinstance(config_data, dict):
            raise HTTPException(status_code=400, detail="MCP配置必须是对象格式")

        # 创建MCP工具记录
        mcp_tool = McpTool.create(
            user_id=user_id,
            name=name,
            config=config_data
        )

        return McpToolResponse(
            id=mcp_tool.id,
            user_id=mcp_tool.user_id,
            name=mcp_tool.name,
            config=mcp_tool.config,
            created_at=mcp_tool.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            updated_at=mcp_tool.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            is_active=mcp_tool.is_active
        )
    except Exception as e:
        logging.exception(f"创建MCP工具时出错: {e}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/mcp/tools", response_model=List[McpToolResponse])
async def get_mcp_tools(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """获取MCP工具列表"""
    try:
        # 如果没有指定user_id，则默认为当前用户
        if user_id is None:
            user_id = current_user.id
        elif current_user.id != user_id:
            raise HTTPException(status_code=403, detail="没有权限访问此用户的MCP工具")

        # 查询MCP工具
        tools = McpTool.select().where(
            (McpTool.user_id == user_id) &
            (McpTool.is_active == 1)
        ).order_by(McpTool.created_at.desc())

        result = [
            McpToolResponse(
                id=tool.id,
                user_id=tool.user_id,
                name=tool.name,
                config=tool.config,
                created_at=tool.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                updated_at=tool.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                is_active=tool.is_active
            )
            for tool in tools
        ]
        
        return result
    except Exception as e:
        logging.exception(f"获取MCP工具列表时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/mcp/tools/{tool_id}", response_model=McpToolResponse)
async def get_mcp_tool(
    tool_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取单个MCP工具"""
    try:
        # 查询MCP工具
        tool = McpTool.get_or_none(McpTool.id == tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="MCP工具不存在")

        # 验证权限
        if tool.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="没有权限访问此MCP工具")

        return McpToolResponse(
            id=tool.id,
            user_id=tool.user_id,
            name=tool.name,
            config=tool.config,
            created_at=tool.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            updated_at=tool.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            is_active=tool.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"获取MCP工具时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.put("/mcp/tools/{tool_id}", response_model=McpToolResponse)
async def update_mcp_tool(
    tool_id: int,
    tool_update: McpToolUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新MCP工具"""
    try:
        # 查询MCP工具
        tool = McpTool.get_or_none(McpTool.id == tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="MCP工具不存在")

        # 验证权限
        if tool.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="没有权限更新此MCP工具")

        # 更新字段
        update_data = tool_update.model_dump(exclude_unset=True)
        if 'config' in update_data:
            # 验证MCP配置格式
            if not isinstance(update_data['config'], dict):
                raise HTTPException(status_code=400, detail="MCP配置必须是对象格式")

        # 更新记录
        query = McpTool.update(**update_data, updated_at=datetime.now()).where(McpTool.id == tool_id)
        query.execute()

        # 获取更新后的记录
        updated_tool = McpTool.get_by_id(tool_id)
        return McpToolResponse(
            id=updated_tool.id,
            user_id=updated_tool.user_id,
            name=updated_tool.name,
            config=updated_tool.config,
            created_at=updated_tool.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            updated_at=updated_tool.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            is_active=updated_tool.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"更新MCP工具时出错: {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/mcp/tools/{tool_id}")
async def delete_mcp_tool(
    tool_id: int,
    current_user: User = Depends(get_current_user)
):
    """删除MCP工具（软删除）"""
    try:
        # 查询MCP工具
        tool = McpTool.get_or_none(McpTool.id == tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="MCP工具不存在")

        # 验证权限
        if tool.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="没有权限删除此MCP工具")

        # 软删除（设置is_active为0）
        query = McpTool.update(is_active=0, updated_at=datetime.now()).where(McpTool.id == tool_id)
        query.execute()

        return {"message": "MCP工具删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"删除MCP工具时出错: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


