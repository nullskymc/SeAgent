import axios from 'axios';
import { ElMessage } from 'element-plus';
import { getToken } from './auth';

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000, // 请求超时时间
});

// 请求拦截器，添加token
api.interceptors.request.use(
  config => {
    const token = getToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data;
  },
  error => {
    console.error('响应错误:', error);
    const message = error.response?.data?.detail || '请求失败，请稍后再试';
    ElMessage.error(message);
    
    // 如果是401未授权，可能需要跳转到登录页
    if (error.response?.status === 401) {
      // 如果是在需要授权的页面，需要跳转到登录页
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;