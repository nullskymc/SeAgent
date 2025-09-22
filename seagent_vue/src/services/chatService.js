import api from './api';
import { getUserInfo } from './auth';

// 获取聊天历史记录
export const getChatHistory = async (userId, skip = 0, limit = 20) => {
  try {
    return await api.get(`/messages/user/${userId}`, {
      params: { skip, limit }
    });
  } catch (error) {
    console.error('获取聊天历史失败:', error);
    throw error;
  }
};

// 获取用户的对话列表
export const getUserChatList = async () => {
  try {
    const userInfo = getUserInfo();
    if (!userInfo || !userInfo.id) {
      throw new Error('用户未登录或无法获取用户ID');
    }
    
    // 使用新的简化路由
    const response = await api.get(`/messages/user-chats/${userInfo.id}`);
    
    // 确保返回的是数组
    if (Array.isArray(response)) {
      return response;
    } else if (response && typeof response === 'object') {
      // 如果返回的是单个对象，将其转换为数组
      return [response];
    } else {
      console.error('获取对话列表返回了意外的数据格式:', response);
      return [];
    }
  } catch (error) {
    console.error('获取对话列表失败:', error);
    throw error;
  }
};

// 创建新对话
export const createNewChat = async (userId, title = '新对话') => {
  try {
    const response = await api.post('/messages/chat', {
      user_id: userId,
      title
    });
    return response;
  } catch (error) {
    console.error('创建新对话失败:', error);
    throw error;
  }
};

// 获取对话详情
export const getChatDetail = async (chatId) => {
  try {
    const response = await api.get(`/messages/chat/${chatId}`);
    return response;
  } catch (error) {
    console.error('获取对话详情失败:', error);
    throw error;
  }
};

// 获取对话的消息列表
export const getChatMessages = async (chatId, skip = 0, limit = 20) => {
  try {
    const response = await api.get(`/messages/chat/${chatId}/messages`, {
      params: { skip, limit }
    });
    return response;
  } catch (error) {
    console.error('获取对话消息失败:', error);
    throw error;
  }
};

// 获取用户的所有对话
export const getUserChats = async (userId) => {
  try {
    const response = await api.get(`/messages/chats/${userId}`);
    return response;
  } catch (error) {
    console.error('获取用户对话列表失败:', error);
    throw error;
  }
};

// 发送消息到指定对话
export const sendMessage = async (chatId, userId, message, role = 'user', collection_name = null) => {
  try {
    let payload = {
      chat_id: chatId,
      message,
      role
    };
    
    // 如果userId存在且不是空，添加到请求中（确保作为字符串类型）
    if (userId !== undefined && userId !== null && userId !== '') {
      // 确保user_id是字符串类型
      payload.user_id = String(userId);
    }
    
    // 如果指定了知识库集合名称，添加到请求中
    if (collection_name) {
      payload.collection_name = collection_name;
    }
    
    const response = await api.post('/api/chat', payload);
    return response;
  } catch (error) {
    console.error('发送消息失败:', error);
    throw error;
  }
};

// 更新对话标题
export const updateChatTitle = async (chatId, newTitle) => {
  try {
    const response = await api.put(`/messages/chat/${chatId}`, {
      title: newTitle
    });
    return response;
  } catch (error) {
    console.error('更新对话标题失败:', error);
    throw error;
  }
};

// 删除对话
export const deleteChat = async (chatId) => {
  try {
    const response = await api.delete(`/messages/chat/${chatId}`);
    return response;
  } catch (error) {
    console.error('删除对话失败:', error);
    throw error;
  }
};

// 创建新会话
export const createNewChatWithMessage = async (userId, title = '新对话', initialMessage = null) => {
  try {
    // 创建新对话
    const newChat = await api.post('/messages/chat', {
      user_id: userId,
      title: title
    });
    
    // 如果有初始消息，发送一条消息开始新会话
    if (initialMessage && newChat.id) {
      await sendMessage(newChat.id, userId, initialMessage, 'user');
    }
    
    return newChat;
  } catch (error) {
    console.error('创建新会话失败:', error);
    throw error;
  }
};

// 获取单个消息
export const getMessage = async (messageId) => {
  try {
    return await api.get(`/messages/${messageId}`);
  } catch (error) {
    console.error('获取消息失败:', error);
    throw error;
  }
};

// 删除消息
export const deleteMessage = async (messageId) => {
  try {
    return await api.delete(`/messages/${messageId}`);
  } catch (error) {
    console.error('删除消息失败:', error);
    throw error;
  }
};

// 为对话生成标题
export const generateChatTitle = async (chatId) => {
  try {
    const response = await api.post(`/api/chats/${chatId}/generate-title`);
    return response;
  } catch (error) {
    console.error('生成标题失败:', error);
    throw error;
  }
};