<template>
  <div class="tool-call-bubble">
    <div class="avatar">
      <el-icon>
        <Tools />
      </el-icon>
    </div>
    <div class="content">
      <div class="header" @click="toggleExpanded">
        <div class="header-left">
          <span class="tool-name">🔧 {{ toolCallData.name }}</span>
          <el-tag :type="getTagType(toolCallData.status)" size="small">
            {{ getStatusText(toolCallData.status) }}
          </el-tag>
        </div>
        <div class="header-right">
          <el-button 
            :icon="expanded ? ArrowDown : ArrowRight" 
            size="small" 
            text 
            @click.stop="toggleExpanded"
          />
        </div>
      </div>
      
      <!-- 抽屉式展开内容 -->
      <el-collapse-transition>
        <div v-show="expanded" class="tool-details">
          <div class="input-section" v-if="toolCallData.input && hasValidInput">
            <div class="section-title">
              <el-icon><DocumentChecked /></el-icon>
              输入参数
            </div>
            <div class="input-content">
              <pre>{{ formatInput(toolCallData.input) }}</pre>
            </div>
          </div>
          
          <div class="output-section" v-if="toolCallData.output && hasValidOutput">
            <div class="section-title">
              <el-icon><SuccessFilled /></el-icon>
              执行结果
            </div>
            <div class="output-content">
              <div v-html="formatOutput(toolCallData.output)"></div>
            </div>
          </div>
          
          <div class="summary-section" v-if="!hasValidOutput && !hasValidInput">
            <div class="section-title">
              <el-icon><InfoFilled /></el-icon>
              工具摘要
            </div>
            <div class="summary-content">
              工具 <code>{{ toolCallData.name }}</code> 已被调用
            </div>
          </div>
        </div>
      </el-collapse-transition>
      
      <div class="timestamp">{{ formatTime(toolCallData.timestamp) }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineProps } from 'vue';
import { Tools, ArrowRight, ArrowDown, DocumentChecked, SuccessFilled, InfoFilled } from '@element-plus/icons-vue';
import dayjs from 'dayjs';

const props = defineProps({
  toolCall: {
    type: Object,
    required: true
  }
});

const expanded = ref(false);

// 从 toolCall prop 中提取实际的工具调用数据
const toolCallData = computed(() => {
  const data = props.toolCall.tool_call || props.toolCall;
  
  console.log('🔧 ToolCallBubble接收到的数据:', JSON.stringify(props.toolCall, null, 2)); // 调试日志
  
  const result = {
    name: data.name || data.tool || data.tool_name || '未知工具',
    input: data.input || data.query || data.tool_input || '',
    output: data.output || data.result || data.response || data.tool_output || '',
    status: data.status || data.tool_status || (data.output ? 'success' : 'pending'),
    timestamp: data.timestamp || new Date().toISOString()
  };
  
  console.log('🔧 ToolCallBubble处理后的数据:', result); // 调试日志
  
  return result;
});

// 检查是否有有效的输入
const hasValidInput = computed(() => {
  const input = toolCallData.value.input;
  return input && input !== '' && input !== '{}' && input !== 'null';
});

// 检查是否有有效的输出
const hasValidOutput = computed(() => {
  const output = toolCallData.value.output;
  return output && output !== '' && output !== '{}' && output !== 'null';
});

// 切换展开/折叠
const toggleExpanded = () => {
  expanded.value = !expanded.value;
};

// 解码UTF编码并格式化输入
const formatInput = (input) => {
  if (!input) return '';
  
  let formatted = input;
  
  // 如果是对象，转换为JSON字符串
  if (typeof input === 'object') {
    formatted = JSON.stringify(input, null, 2);
  }
  
  // 解码Unicode字符
  try {
    formatted = decodeUnicodeEscapes(formatted);
  } catch (e) {
    console.warn('解码Unicode失败:', e);
  }
  
  return formatted;
};

// 解码UTF编码并格式化输出
const formatOutput = (output) => {
  if (!output) return '';
  
  let formatted = output;
  
  // 如果是对象，转换为JSON字符串
  if (typeof output === 'object') {
    formatted = JSON.stringify(output, null, 2);
  }
  
  // 解码Unicode字符
  try {
    formatted = decodeUnicodeEscapes(formatted);
  } catch (e) {
    console.warn('解码Unicode失败:', e);
    formatted = output; // 解码失败时使用原始输出
  }
  
  // 将换行符转换为HTML换行
  formatted = formatted.replace(/\n/g, '<br>');
  
  // 简单的代码块高亮
  formatted = formatted.replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>');
  formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
  
  return formatted;
};

// 解码Unicode转义序列
const decodeUnicodeEscapes = (str) => {
  if (typeof str !== 'string') return str;
  
  // 解码 \uXXXX 格式的Unicode字符
  return str.replace(/\\u[\dA-Fa-f]{4}/g, (match) => {
    return String.fromCharCode(parseInt(match.replace(/\\u/g, ''), 16));
  });
};

// 获取状态对应的标签类型
const getTagType = (status) => {
  switch (status) {
    case 'success':
    case 'completed':
      return 'success';
    case 'error':
    case 'failed':
      return 'danger';
    case 'pending':
    case 'running':
    case 'started':
      return 'warning';
    default:
      return 'info';
  }
};

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    'pending': '执行中',
    'started': '已启动',
    'running': '运行中',
    'success': '成功',
    'completed': '已完成',
    'error': '失败',
    'failed': '失败'
  };
  return statusMap[status] || status;
};

// 格式化时间
const formatTime = (date) => {
  if (!date) return dayjs().format('HH:mm:ss');
  return dayjs(date).format('HH:mm:ss');
};
</script>

<style scoped>
.tool-call-bubble {
  display: flex;
  max-width: 90%;
  margin-bottom: 16px;
  position: relative;
  opacity: 1;
  animation: slideInLeft 0.4s ease-out;
}

.tool-call-bubble .avatar {
  width: 40px;
  height: 40px;
  margin: 0 12px;
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 4px;
}

.tool-call-bubble .avatar .el-icon {
  font-size: 24px;
  color: var(--el-color-success);
  background: var(--el-color-success-light-9);
  border-radius: 50%;
  padding: 8px;
  border: 2px solid var(--el-color-success-light-7);
  box-shadow: 0 2px 6px rgba(103, 194, 58, 0.3);
}

.tool-call-bubble .content {
  flex: 1;
  border-radius: 12px;
  max-width: 100%;
  position: relative;
  background: linear-gradient(135deg, var(--el-color-success-light-9) 0%, #f0f9ff 100%);
  border: 1px solid var(--el-color-success-light-6);
  transition: all 0.3s ease;
  box-shadow: 0 2px 12px rgba(103, 194, 58, 0.1);
}

.tool-call-bubble:hover .content {
  border-color: var(--el-color-success-light-4);
  box-shadow: 0 4px 20px rgba(103, 194, 58, 0.15);
  transform: translateY(-2px);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
  border-radius: 12px;
}

.header:hover {
  background: var(--el-color-success-light-8);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
}

.tool-name {
  font-weight: 600;
  color: var(--el-color-success-dark-2);
  font-size: 14px;
  margin-right: 8px;
}

.tool-details {
  padding: 0 16px 12px;
  border-top: 1px solid var(--el-color-success-light-8);
  margin-top: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  margin: 12px 0 8px 0;
  color: var(--el-text-color-primary);
  font-size: 13px;
}

.section-title .el-icon {
  font-size: 14px;
  color: var(--el-color-success);
}

.input-content {
  background: var(--el-fill-color-light);
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid var(--el-border-color-lighter);
}

.input-content pre {
  margin: 0;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Fira Mono', 'Droid Sans Mono', 'Source Code Pro', monospace;
  font-size: 12px;
  line-height: 1.4;
  color: var(--el-text-color-regular);
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
}

.output-content {
  background: var(--el-bg-color-overlay);
  border-radius: 6px;
  padding: 12px;
  border: 1px solid var(--el-border-color-lighter);
  line-height: 1.6;
  font-size: 13px;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.output-content :deep(code) {
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
  font-size: 12px;
  color: var(--el-color-primary);
}

.output-content :deep(pre) {
  background: var(--el-fill-color-darker);
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
  border-left: 3px solid var(--el-color-primary);
}

.output-content :deep(pre code) {
  background: transparent;
  padding: 0;
  font-size: 12px;
  line-height: 1.4;
}

.summary-section {
  margin-top: 12px;
}

.summary-content {
  background: var(--el-fill-color-blank);
  border-radius: 6px;
  padding: 12px;
  border: 1px solid var(--el-border-color-lighter);
  font-size: 13px;
  color: var(--el-text-color-regular);
  font-style: italic;
}

.summary-content code {
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: var(--el-color-success);
  font-style: normal;
}

.timestamp {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  text-align: right;
  padding: 0 16px 12px;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Dark mode adjustments */
:root.dark .tool-call-bubble .content,
html.dark .tool-call-bubble .content,
.el-html--dark .tool-call-bubble .content {
  background: var(--el-color-success-dark-2);
  border-color: var(--el-color-success-light-3);
}

:root.dark .tool-call-bubble .avatar .el-icon,
html.dark .tool-call-bubble .avatar .el-icon,
.el-html--dark .tool-call-bubble .avatar .el-icon {
  background: var(--el-color-success-light-8);
  border-color: var(--el-color-success-light-6);
}

:root.dark .header:hover,
html.dark .header:hover,
.el-html--dark .header:hover {
  background: var(--el-color-success-dark-1);
}

:root.dark .tool-details,
html.dark .tool-details,
.el-html--dark .tool-details {
  border-top-color: var(--el-color-success-light-6);
}

:root.dark .input-content,
html.dark .input-content,
.el-html--dark .input-content {
  background: var(--el-fill-color-dark);
  border-color: var(--el-border-color-dark);
}

:root.dark .output-content,
html.dark .output-content,
.el-html--dark .output-content {
  background: var(--el-bg-color);
  border-color: var(--el-border-color-dark);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .tool-call-bubble {
    max-width: 95%;
  }
  
  .header {
    padding: 10px 12px;
  }
  
  .tool-details {
    padding: 0 12px 10px;
  }
  
  .tool-name {
    font-size: 13px;
  }
}
</style>