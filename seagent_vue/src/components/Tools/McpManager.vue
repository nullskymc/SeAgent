<template>
  <el-card class="mcp-manager-card">
    <template #header>
      <div class="card-header">
        <h3>MCP工具管理</h3>
        <el-tag type="success" effect="plain">新增功能</el-tag>
      </div>
    </template>

    <div class="mcp-manager-content">
      <!-- 工具列表 -->
      <div class="tools-section">
        <div class="section-header">
          <h4>已保存的MCP工具</h4>
          <el-button
            type="primary"
            size="small"
            @click="refreshTools"
            :loading="loading"
          >
            刷新
          </el-button>
        </div>

        <el-table
          :data="mcpTools"
          v-loading="loading"
          empty-text="暂无MCP工具"
          style="width: 100%"
        >
          <el-table-column prop="name" label="工具名称" width="180" />
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column label="操作" width="150">
            <template #default="scope">
              <el-button
                size="small"
                type="danger"
                @click="deleteTool(scope.row.id)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 添加新工具 -->
      <div class="add-tool-section">
        <h4>添加新的MCP工具</h4>
        <p class="description">在输入框中粘贴MCP JSON配置，扩展AI助手的能力</p>

        <div class="upload-area">
          <el-form
            :model="uploadForm"
            :rules="uploadRules"
            ref="uploadFormRef"
            label-width="80px"
          >
            <el-form-item label="工具名称" prop="name">
              <el-input
                v-model="uploadForm.name"
                placeholder="请输入工具名称"
              />
            </el-form-item>

            <el-form-item label="JSON配置" prop="config">
              <el-input
                v-model="uploadForm.config"
                type="textarea"
                :rows="8"
                placeholder="请粘贴MCP JSON配置，例如：
{
  &quot;calculator&quot;: {
    &quot;transport&quot;: &quot;stdio&quot;,
    &quot;command&quot;: &quot;python&quot;,
    &quot;args&quot;: [&quot;-c&quot;, &quot;import sys; print('Calculator MCP server started'); sys.stdout.flush()&quot;]
  }
}"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="submitConfig"
                :loading="uploading"
              >
                提交MCP工具
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>

      <!-- 功能说明 -->
      <div class="feature-list">
        <div class="feature-item">
          <el-icon><Upload /></el-icon>
          <span>上传MCP配置文件</span>
        </div>
        <div class="feature-item">
          <el-icon><Tools /></el-icon>
          <span>管理已保存的工具</span>
        </div>
        <div class="feature-item">
          <el-icon><Connection /></el-icon>
          <span>扩展AI助手工具能力</span>
        </div>
      </div>

      <!-- 结果提示 -->
      <div v-if="resultMessage" class="result-message">
        <el-alert
          :type="resultMessage.type"
          :title="resultMessage.message"
          show-icon
          :closable="false"
        />
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { UploadFilled, Upload, Tools, Connection } from '@element-plus/icons-vue';
import { getUserInfo } from '@/services/auth';
import api from '@/services/api';

// 状态管理
const userId = ref(null);
const mcpTools = ref([]);
const loading = ref(false);
const uploading = ref(false);
const resultMessage = ref(null);

// 表单数据
const uploadForm = ref({
  name: '',
  config: ''
});

const uploadFormRef = ref(null);

// 表单验证规则
const uploadRules = {
  name: [
    { required: true, message: '请输入工具名称', trigger: 'blur' }
  ],
  config: [
    { required: true, message: '请输入JSON配置', trigger: 'blur' },
    { validator: validateJson, trigger: 'blur' }
  ]
};

// JSON格式验证器
const validateJson = (rule, value, callback) => {
  if (!value) {
    callback();
    return;
  }

  try {
    const parsed = JSON.parse(value);
    if (typeof parsed !== 'object') {
      callback(new Error('JSON配置必须是对象格式'));
    } else {
      callback();
    }
  } catch (error) {
    callback(new Error('JSON格式无效'));
  }
};

// 获取用户信息
const userInfo = getUserInfo();
if (userInfo) {
  userId.value = userInfo.id;
}

// 获取MCP工具列表
const fetchTools = async () => {
  if (!userId.value) return;

  loading.value = true;
  try {
    mcpTools.value = await api.get(`/mcp/tools?user_id=${userId.value}`);
  } catch (error) {
    ElMessage.error('获取MCP工具列表失败');
    console.error('获取MCP工具列表失败:', error);
  } finally {
    loading.value = false;
  }
};

// 刷新工具列表
const refreshTools = () => {
  fetchTools();
};

// 提交JSON配置
const submitConfig = async () => {
  if (!uploadFormRef.value) return;

  await uploadFormRef.value.validate(async (valid) => {
    if (!valid) return;

    if (!userId.value) {
      ElMessage.error('用户信息无效');
      return;
    }

    uploading.value = true;
    try {
      const response = await api.post('/mcp/tools', {
        user_id: userId.value,
        name: uploadForm.value.name,
        config: uploadForm.value.config
      });

      resultMessage.value = {
        type: 'success',
        message: 'MCP工具提交成功'
      };

      ElMessage.success('MCP工具提交成功');

      // 重置表单
      uploadForm.value.name = '';
      uploadForm.value.config = '';

      // 刷新工具列表
      await fetchTools();
    } catch (error) {
      resultMessage.value = {
        type: 'error',
        message: error.response?.data?.detail || 'MCP工具提交失败'
      };
      ElMessage.error(error.response?.data?.detail || 'MCP工具提交失败');
    } finally {
      uploading.value = false;
    }
  });
};

// 删除工具
const deleteTool = async (toolId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个MCP工具吗？', '确认删除', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    });

    await api.delete(`/mcp/tools/${toolId}`);

    ElMessage.success('MCP工具删除成功');

    // 刷新工具列表
    await fetchTools();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除MCP工具失败');
      console.error('删除MCP工具失败:', error);
    }
  }
};

// 组件挂载时获取工具列表
onMounted(() => {
  fetchTools();
});
</script>

<style scoped>
.mcp-manager-card {
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

.mcp-manager-content {
  padding: 10px 0;
}

.tools-section {
  margin-bottom: 30px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-header h4 {
  margin: 0;
}

.add-tool-section {
  margin-bottom: 30px;
}

.add-tool-section h4 {
  margin-bottom: 10px;
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