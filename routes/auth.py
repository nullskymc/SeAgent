from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Query, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any, Optional

from database.auth import create_access_token
from database.models.user import User, UserCreate, LoginRequest, TokenResponse, UserResponse, pwd_context

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


@router.post("/register", response_model=Dict[str, Any])
def register(user_create: UserCreate):
    """用户注册接口"""
    user = User.get_or_none(User.user_id == user_create.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被注册",
        )
    user = User.get_or_none(User.email == user_create.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册",
        )
    new_user = User(user_id=user_create.username, email=user_create.email)
    new_user.set_password(user_create.password)
    new_user.save()
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": new_user.user_id}, expires_delta=access_token_expires
    )
    
    # 返回令牌和用户信息
    return {
        "token": TokenResponse(access_token=access_token, token_type="bearer"),
        "user": {
            "id": new_user.id,
            "username": new_user.user_id,
            "email": new_user.email
        }
    }


@router.post("/login", response_model=Dict[str, Any])
def login(login_request: LoginRequest):
    """用户登录接口"""
    # 登录处理
    
    user = User.get_or_none(User.user_id == login_request.username)
    
    if not user:
        # 用户不存在
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not pwd_context.verify(login_request.password, user.user_password):
        # 密码验证失败
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.user_id}, expires_delta=access_token_expires
    )
    
    # 返回令牌和用户信息
    return {
        "token": TokenResponse(access_token=access_token, token_type="bearer"),
        "user": {
            "id": user.id,
            "username": user.user_id,
            "email": user.email
        }
    }

# 添加GET登录页面的路由，避免404错误
@router.get("/login")
def login_page():
    """登录页面"""
    return {"message": "请使用POST方法提交登录表单"}


def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前登录用户"""
    from database.auth import SECRET_KEY, ALGORITHM
    from jose import jwt, JWTError

    # 检查token是否存在
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = User.get_or_none(User.user_id == username)
    if user is None:
        raise credentials_exception
    return user


def get_user_id_from_token(token: Optional[str] = Depends(oauth2_scheme)):
    """简化的用户ID获取函数，从token中提取用户ID，失败时不报错而是返回None"""
    if not token:
        return None
        
    from database.auth import SECRET_KEY, ALGORITHM
    from jose import jwt, JWTError
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return None
        user = User.get_or_none(User.user_id == username)
        return user.id if user else None
    except JWTError:
        return None


def get_user_id(
    token: Optional[str] = Depends(oauth2_scheme), 
    user_id: Optional[int] = Query(None, description="用户ID，如未提供则尝试从token获取")
):
    """获取用户ID，优先使用query参数，其次尝试从token中获取"""
    if user_id is not None:
        return user_id
    
    token_user_id = get_user_id_from_token(token)
    return token_user_id