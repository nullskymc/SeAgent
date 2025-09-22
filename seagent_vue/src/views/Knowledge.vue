<template>
  <div class="knowledge-container">
    <Header />
    
    <div class="content-wrapper">
      <div class="content-container">
        <h1>知识库管理</h1>
        
        <!-- 上传文件表单 -->
        <el-card class="upload-card">
          <template #header>
            <div class="card-header">
              <h3>上传文件到知识库</h3>
            </div>
          </template>
          
          <el-form :model="uploadForm" label-width="100px">
            <el-form-item label="知识库名称">
              <el-input v-model="uploadForm.collectionName" placeholder="输入知识库名称" />
            </el-form-item>
            
            <el-form-item label="选择文件">
              <el-upload
                class="file-uploader"
                drag
                :auto-upload="false"
                :limit="1"
                :on-change="handleFileChange"
                :on-exceed="handleExceed"
                :file-list="uploadForm.fileList"
              >
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  拖拽文件到此处或 <em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    支持的文件类型: TXT, PDF, CSV
                  </div>
                </template>
              </el-upload>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="submitUpload" :loading="uploading">
                上传到知识库
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 知识库列表 -->
        <el-card class="collections-card">
          <template #header>
            <div class="card-header">
              <h3>我的知识库</h3>
              <el-button type="primary" @click="refreshCollections" :loading="loading" size="small">
                刷新列表
              </el-button>
            </div>
          </template>
          
          <div v-if="loading" class="loading-container">
            <el-icon class="is-loading"><loading /></el-icon>
            <span>加载知识库...</span>
          </div>
          
          <div v-else-if="collections.length === 0" class="empty-container">
            <el-empty description="暂无知识库" />
          </div>
          
          <el-table v-else :data="collections" style="width: 100%">
            <el-table-column prop="name" label="知识库名称" />
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button
                  type="danger"
                  size="small"
                  @click="confirmDelete(scope.row)"
                  :loading="scope.row.deleting"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </div>
    
    <!-- 确认删除对话框 -->
    <el-dialog
      v-model="deleteDialog.visible"
      title="确认删除"
      width="30%"
      :close-on-click-modal="false"
    >
      <span>确定要删除知识库 "{{ deleteDialog.collection }}" 吗？此操作不可恢复。</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteDialog.visible = false">取消</el-button>
          <el-button type="danger" @click="handleDelete" :loading="deleteDialog.loading">
            删除
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { UploadFilled, Loading } from '@element-plus/icons-vue';
import Header from '@/components/Chat/Header.vue';
import { uploadKnowledgeFile, getKnowledgeCollections, deleteKnowledgeCollection } from '@/services/knowledgeService';

// 上传表单数据
const uploadForm = ref({
  collectionName: '',
  file: null,
  fileList: []
});

// 知识库集合列表
const collections = ref([]);
const loading = ref(false);
const uploading = ref(false);

// 删除对话框
const deleteDialog = ref({
  visible: false,
  collection: '',
  loading: false
});

// 处理文件选择
const handleFileChange = (file) => {
  uploadForm.value.file = file.raw;
};

// 处理文件超出限制
const handleExceed = () => {
  ElMessage.warning('一次只能上传一个文件');
};

// 提交上传
const submitUpload = async () => {
  // 表单验证
  if (!uploadForm.value.collectionName) {
    ElMessage.warning('请输入知识库名称');
    return;
  }
  
  if (!uploadForm.value.file) {
    ElMessage.warning('请选择要上传的文件');
    return;
  }
  
  try {
    uploading.value = true;
    const response = await uploadKnowledgeFile(
      uploadForm.value.file, 
      uploadForm.value.collectionName
    );
    
    ElMessage.success(response.message || '上传成功');
    
    // 清空表单
    uploadForm.value.collectionName = '';
    uploadForm.value.file = null;
    uploadForm.value.fileList = [];
    
    // 刷新知识库列表
    await refreshCollections();
    
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '上传失败，请稍后重试');
  } finally {
    uploading.value = false;
  }
};

// 获取知识库集合列表
const refreshCollections = async () => {
  try {
    loading.value = true;
    const collectionsList = await getKnowledgeCollections();
    collections.value = collectionsList.map(name => ({ name, deleting: false }));
  } catch (error) {
    ElMessage.error('获取知识库列表失败');
  } finally {
    loading.value = false;
  }
};

// 确认删除
const confirmDelete = (collection) => {
  deleteDialog.value.collection = collection.name;
  deleteDialog.value.visible = true;
};

// 处理删除
const handleDelete = async () => {
  try {
    deleteDialog.value.loading = true;
    
    // 找到对应的集合并设置删除状态
    const collectionItem = collections.value.find(c => c.name === deleteDialog.value.collection);
    if (collectionItem) {
      collectionItem.deleting = true;
    }
    
    await deleteKnowledgeCollection(deleteDialog.value.collection);
    
    ElMessage.success(`已删除知识库: ${deleteDialog.value.collection}`);
    deleteDialog.value.visible = false;
    
    // 从列表中移除
    collections.value = collections.value.filter(
      c => c.name !== deleteDialog.value.collection
    );
    
  } catch (error) {
    ElMessage.error('删除知识库失败');
  } finally {
    deleteDialog.value.loading = false;
    
    // 重置所有集合的删除状态
    collections.value.forEach(c => {
      c.deleting = false;
    });
  }
};

// 页面加载时获取知识库列表
onMounted(() => {
  refreshCollections();
});
</script>

<style scoped>
.knowledge-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  /* 页面由内容区域承担滚动，根容器不滚动以避免嵌套滚动冲突 */
  overflow: hidden;
  position: relative;
}

.content-wrapper {
  position: absolute;
  top: 60px; /* 为固定头部留出空间 */
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: auto;
}

.content-container {
  padding: 20px 24px 24px;
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
  /* 由 content-wrapper 负责滚动，这里不再设置滚动 */
}

h1 {
  margin-bottom: 24px;
  font-size: 28px;
  color: var(--el-text-color-primary);
}

.upload-card,
.collections-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
}

.file-uploader {
  width: 100%;
}

.loading-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  color: var(--el-text-color-secondary);
}

.loading-container {
  gap: 12px;
}
</style>