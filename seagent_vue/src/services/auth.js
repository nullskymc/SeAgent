import api from './api';

const TOKEN_KEY = 'seagent_token';
const USER_INFO_KEY = 'seagent_user';

// 保存token到本地存储
export const saveToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token);
};

// 从本地存储获取token
export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

// 删除本地存储的token
export const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_INFO_KEY);
};

// 保存用户信息
export const saveUserInfo = (userInfo) => {
  localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
};

// 获取用户信息
export const getUserInfo = () => {
  const userInfo = localStorage.getItem(USER_INFO_KEY);
  return userInfo ? JSON.parse(userInfo) : null;
};

// 用户登录
export const login = async (username, password) => {
  try {
    const response = await api.post('/auth/login', {
      username,
      password
    });
    
    // 处理新的响应格式
    if (response.token && response.user) {
      saveToken(response.token.access_token);
      saveUserInfo(response.user);
      return response;
    } else if (response.access_token) {
      // 兼容旧格式
      saveToken(response.access_token);
      return response;
    } else {
      throw new Error('登录响应格式不正确');
    }
  } catch (error) {
    console.error('登录失败:', error);
    throw error;
  }
};

// 用户注册
export const register = async (username, password, email) => {
  try {
    const response = await api.post('/auth/register', {
      username,
      password,
      email
    });
    
    // 处理新的响应格式
    if (response.token && response.user) {
      saveToken(response.token.access_token);
      saveUserInfo(response.user);
      return response;
    } else if (response.access_token) {
      // 兼容旧格式
      saveToken(response.access_token);
      return response;
    } else {
      throw new Error('注册响应格式不正确');
    }
  } catch (error) {
    console.error('注册失败:', error);
    throw error;
  }
};

// 退出登录
export const logout = () => {
  removeToken();
  // 可以在这里添加跳转到登录页面的逻辑
};

// 检查用户是否已登录
export const isAuthenticated = () => {
  return !!getToken();
};