<template>
  <div class="mcp-tools-container">
    <Header />

    <div class="content-wrapper">
      <div class="content-container">
        <h1>MCP工具管理</h1>

        <div class="mcp-content">
          <!-- 工具列表 -->
          <div class="tools-section">
            <div class="section-header">
              <h2>已保存的MCP工具</h2>
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
            <h2>添加新的MCP工具</h2>
            <p class="description">在输入框中粘贴MCP JSON配置，扩展AI助手的能力</p>

            <div class="form-area">
              <el-form
                :model="uploadForm"
                :rules="uploadRules"
                ref="uploadFormRef"
                label-width="100px"
              >
                <el-form-item label="工具名称" prop="name">
                  <el-input
                    v-model="uploadForm.name"
                    placeholder="请输入工具名称，如：calculator"
                  />
                </el-form-item>

                <el-form-item label="JSON配置" prop="config">
                  <el-input
                    v-model="uploadForm.config"
                    type="textarea"
                    :rows="12"
                    placeholder="请粘贴MCP JSON配置，例如：
{
  &quot;calculator&quot;: {
    &quot;transport&quot;: &quot;stdio&quot;,
    &quot;command&quot;: &quot;python&quot;,
    &quot;args&quot;: [&quot;-c&quot;, &quot;import sys; print(&apos;Calculator MCP server started&apos;); sys.stdout.flush()&quot;]
  },
  &quot;web_search&quot;: {
    &quot;transport&quot;: &quot;streamable_http&quot;,
    &quot;url&quot;: &quot;http://localhost:8080/mcp&quot;
  }
}"
                  />
                </el-form-item>

                <el-form-item>
                  <el-button
                    type="primary"
                    @click="submitConfig"
                    :loading="uploading"
                    size="large"
                  >
                    提交MCP工具
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>

          <!-- 功能说明 -->
          <div class="info-section">
            <h2>功能说明</h2>
            <div class="info-cards">
              <el-card class="info-card">
                <template #header>
                  <div class="card-header">
                    <el-icon><Upload /></el-icon>
                    <span>便捷配置</span>
                  </div>
                </template>
                <p>直接粘贴JSON配置，无需文件上传</p>
              </el-card>

              <el-card class="info-card">
                <template #header>
                  <div class="card-header">
                    <el-icon><Tools /></el-icon>
                    <span>工具管理</span>
                  </div>
                </template>
                <p>查看和管理所有已保存的MCP工具</p>
              </el-card>

              <el-card class="info-card">
                <template #header>
                  <div class="card-header">
                    <el-icon><Connection /></el-icon>
                    <span>实时生效</span>
                  </div>
                </template>
                <p>提交后立即在对话中生效，扩展AI能力</p>
              </el-card>
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Upload, Tools, Connection } from '@element-plus/icons-vue';
import { getUserInfo } from '@/services/auth';
import api from '@/services/api';
import Header from '@/components/Chat/Header.vue';

// 获取用户信息
const userInfo = getUserInfo();

// 状态管理
const userId = ref(userInfo ? userInfo.id : null);
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
  } catch (jsonError) {
    callback(new Error('JSON格式无效'));
  }
};

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

// 获取MCP工具列表
const fetchTools = async () => {
  if (!userId.value) return;

  loading.value = true;
  try {
    const response = await api.get(`/mcp/tools?user_id=${userId.value}`);
    // 确保返回的是数组格式
    mcpTools.value = Array.isArray(response) ? response : [];
  } catch (fetchError) {
    ElMessage.error('获取MCP工具列表失败');
    console.error('获取MCP工具列表失败:', fetchError);
    mcpTools.value = []; // 确保在错误情况下也设置为空数组
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
      // 使用FormData提交表单数据，因为后端API期望表单格式
      const formData = new FormData();
      formData.append('user_id', userId.value.toString());
      formData.append('name', uploadForm.value.name);
      formData.append('config', uploadForm.value.config);
      
      const response = await api.post('/mcp/tools', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
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
    } catch (submitError) {
      resultMessage.value = {
        type: 'error',
        message: submitError.response?.data?.detail || 'MCP工具提交失败'
      };
      ElMessage.error(submitError.response?.data?.detail || 'MCP工具提交失败');
    } finally {
      uploading.value = false;
    }
  });
};

// 删除工具
const deleteTool = async (toolId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个MCP工具吗？删除后该工具将不再在对话中生效。', '确认删除', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    });

    await api.delete(`/mcp/tools/${toolId}`);

    ElMessage.success('MCP工具删除成功');

    // 刷新工具列表
    await fetchTools();
  } catch (deleteError) {
    if (deleteError !== 'cancel') {
      ElMessage.error('删除MCP工具失败');
      console.error('删除MCP工具失败:', deleteError);
    }
  }
};

// 组件挂载时获取工具列表
onMounted(() => {
  fetchTools();
});
</script>

<style scoped>
.mcp-tools-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.content-wrapper {
  position: absolute;
  top: 60px;
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: auto;
}

.content-container {
  padding: 20px 24px 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

h1 {
  margin-bottom: 32px;
  font-size: 32px;
  color: var(--el-text-color-primary);
}

h2 {
  margin-bottom: 20px;
  font-size: 24px;
  color: var(--el-text-color-primary);
}

.mcp-content {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.tools-section {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  margin: 0;
  font-size: 20px;
}

.add-tool-section {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.description {
  margin-bottom: 24px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  font-size: 16px;
}

.form-area {
  max-width: 800px;
}

.info-section {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.info-card {
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.card-header .el-icon {
  font-size: 20px;
  color: var(--el-color-primary);
}

.info-card p {
  margin: 0;
  color: var(--el-text-color-regular);
  line-height: 1.5;
}

.result-message {
  margin-top: 20px;
  max-width: 600px;
}

/* 暗黑模式适配 */
:root.dark .tools-section,
:root.dark .add-tool-section,
:root.dark .info-section,
html.dark .tools-section,
html.dark .add-tool-section,
html.dark .info-section,
.el-html--dark .tools-section,
.el-html--dark .add-tool-section,
.el-html--dark .info-section {
  background-color: var(--el-bg-color-page);
}
</style>