<template>
  <div class="tool-call-bubble" :class="toolCallData.status">
    <div class="avatar">
      <el-icon>
        <Tools />
      </el-icon>
    </div>
    <div class="content">
      <div class="header">
        <span class="tool-name">{{ toolCallData.name }}</span>
        <span class="status" :class="toolCallData.status">{{ getStatusText(toolCallData.status) }}</span>
      </div>
      <div class="tool-details">
        <div class="input-section" v-if="toolCallData.input">
          <div class="section-title">输入参数</div>
          <pre class="input-content">{{ formatJson(toolCallData.input) }}</pre>
        </div>
        <div class="output-section" v-if="toolCallData.output">
          <div class="section-title">执行结果</div>
          <div class="output-content">{{ toolCallData.output }}</div>
        </div>
      </div>
      <div class="timestamp">{{ formatTime(toolCallData.timestamp) }}</div>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';
import { Tools } from '@element-plus/icons-vue';
import dayjs from 'dayjs';

const props = defineProps({
  toolCall: {
    type: Object,
    required: true
  }
});

// 从 toolCall prop 中提取实际的工具调用数据
const toolCallData = props.toolCall.tool_call || props.toolCall;

// 格式化JSON显示
const formatJson = (obj) => {
  if (typeof obj === 'string') {
    try {
      return JSON.stringify(JSON.parse(obj), null, 2);
    } catch {
      return obj;
    }
  }
  return JSON.stringify(obj, null, 2);
};

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    'pending': '执行中',
    'success': '执行成功',
    'error': '执行失败'
  };
  return statusMap[status] || status;
};

// 格式化时间
const formatTime = (date) => {
  if (!date) return '';
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
};
</script>

<style scoped>
.tool-call-bubble {
  display: flex;
  max-width: 85%;
  margin-bottom: 20px;
  position: relative;
  opacity: 1;
  animation: fadeIn 0.3s ease-out;
}

.tool-call-bubble .avatar {
  width: 36px;
  height: 36px;
  margin: 0 12px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tool-call-bubble .avatar .el-icon {
  font-size: 24px;
  color: var(--el-color-success);
  background: var(--el-color-success-light-9);
  border-radius: 50%;
  padding: 6px;
}

.tool-call-bubble .content {
  flex: 1;
  padding: 16px;
  border-radius: 16px;
  max-width: 100%;
  position: relative;
  transition: all 0.2s ease;
  background: var(--el-bg-color-overlay);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--el-border-color-light);
}

.tool-call-bubble:hover .content {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  border-color: var(--el-border-color-base);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.tool-name {
  font-weight: 600;
  color: var(--el-color-success);
}

.status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  background: var(--el-color-info-light-9);
  color: var(--el-color-info);
}

.status.success {
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.status.pending {
  background: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}

.status.error {
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}

.tool-details {
  font-size: 14px;
}

.section-title {
  font-weight: 600;
  margin: 12px 0 6px 0;
  color: var(--el-text-color-primary);
}

.input-content,
.output-content {
  background: var(--el-fill-color-light);
  border-radius: 4px;
  padding: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.input-content {
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
}

.output-content {
  line-height: 1.5;
}

.timestamp {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-top: 12px;
  text-align: right;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Dark mode adjustments */
:root.dark .tool-call-bubble .content,
html.dark .tool-call-bubble .content,
.el-html--dark .tool-call-bubble .content {
  background: var(--el-bg-color-overlay);
  border-color: var(--el-border-color-base);
}

:root.dark .tool-call-bubble .avatar .el-icon,
html.dark .tool-call-bubble .avatar .el-icon,
.el-html--dark .tool-call-bubble .avatar .el-icon {
  background: var(--el-color-success-light-8);
}
</style>