import api from './api';

// 上传文件到知识库
export const uploadKnowledgeFile = async (file, collectionName) => {
  try {
    // 创建FormData对象
    const formData = new FormData();
    formData.append('file', file);
    formData.append('collection_name', collectionName);
    
    // 设置上传进度处理
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    };
    
    const response = await api.post('/knowledge/upload', formData, config);
    return response;
  } catch (error) {
    console.error('上传知识库文件失败:', error);
    throw error;
  }
};

// 获取知识库集合列表
export const getKnowledgeCollections = async () => {
  try {
    const response = await api.get('/knowledge/collections');
    return response.collections || [];
  } catch (error) {
    console.error('获取知识库集合失败:', error);
    throw error;
  }
};

// 删除知识库集合
export const deleteKnowledgeCollection = async (collectionName) => {
  try {
    const response = await api.delete(`/knowledge/collections/${collectionName}`);
    return response;
  } catch (error) {
    console.error('删除知识库集合失败:', error);
    throw error;
  }
};