<template>
  <el-card class="mcp-card">
    <template #header>
      <div class="card-header">
        <h3>MCP工具配置</h3>
        <el-tag type="success" effect="plain">新增功能</el-tag>
      </div>
    </template>

    <div class="mcp-content">
      <p class="description">上传MCP JSON配置文件，扩展AI助手的能力</p>

      <div class="upload-area">
        <el-upload
          class="upload-demo"
          drag
          action="/api/mcp/upload"
          :auto-upload="false"
          :on-change="handleChange"
          :on-success="handleSuccess"
          :on-error="handleError"
          :data="{ user_id: userId }"
          accept=".json"
        >
          <el-icon class="el-icon--upload">
            <UploadFilled />
          </el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              请上传MCP配置JSON文件，文件大小不超过1MB
            </div>
          </template>
        </el-upload>
      </div>

      <div class="feature-list">
        <div class="feature-item">
          <el-icon><Upload /></el-icon>
          <span>上传MCP配置文件</span>
        </div>
        <div class="feature-item">
          <el-icon><Tools /></el-icon>
          <span>扩展AI助手工具能力</span>
        </div>
        <div class="feature-item">
          <el-icon><Connection /></el-icon>
          <span>连接外部服务和工具</span>
        </div>
      </div>

      <div v-if="uploadResult" class="result-message">
        <el-alert
          :type="uploadResult.type"
          :title="uploadResult.message"
          show-icon
          :closable="false"
        />
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { UploadFilled, Upload, Tools, Connection } from '@element-plus/icons-vue';
import { getUserInfo } from '@/services/auth';

const userId = ref(null);
const uploadResult = ref(null);

// 获取用户ID
const userInfo = getUserInfo();
if (userInfo) {
  userId.value = userInfo.id;
}

const handleChange = (file, fileList) => {
  // 验证文件类型
  if (!file.name.endsWith('.json')) {
    ElMessage.error('只支持JSON文件');
    return false;
  }

  // 验证文件大小（1MB限制）
  if (file.size > 1024 * 1024) {
    ElMessage.error('文件大小不能超过1MB');
    return false;
  }

  return true;
};

const handleSuccess = (response, file, fileList) => {
  uploadResult.value = {
    type: 'success',
    message: 'MCP配置文件上传成功'
  };
  ElMessage.success('MCP配置文件上传成功');
};

const handleError = (error, file, fileList) => {
  uploadResult.value = {
    type: 'error',
    message: 'MCP配置文件上传失败'
  };
  ElMessage.error('MCP配置文件上传失败');
};
</script>

<style scoped>
.mcp-card {
  height: 100%;
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

.mcp-content {
  padding: 10px 0;
}

.description {
  margin-bottom: 20px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
}

.upload-area {
  margin-bottom: 20px;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.feature-item .el-icon {
  font-size: 18px;
  color: var(--el-color-primary);
}

.result-message {
  margin-top: 20px;
}
</style>