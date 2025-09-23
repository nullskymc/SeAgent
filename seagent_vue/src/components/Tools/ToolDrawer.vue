<template>
  <el-drawer
    v-model="isVisible"
    title="工具调用详情"
    direction="rtl"
    size="400px"
    :before-close="handleClose"
  >
    <div class="tool-drawer-content">
      <div v-if="processedToolCalls.length === 0" class="empty-state">
        <el-empty description="暂无工具调用信息" />
      </div>
      <div v-else class="tool-calls-list">
        <div
          v-for="(toolCall, index) in processedToolCalls"
          :key="index"
          class="tool-call-item"
        >
          <div class="tool-call-header">
            <el-tag :type="getToolTagType(toolCall.status)">
              {{ toolCall.status }}
            </el-tag>
            <span class="tool-name">{{ toolCall.name }}</span>
          </div>
          <div class="tool-call-details">
            <div class="tool-call-input" v-if="toolCall.input">
              <h4>输入参数:</h4>
              <pre>{{ toolCall.input }}</pre>
            </div>
            <div class="tool-call-output" v-if="toolCall.output">
              <h4>输出结果:</h4>
              <pre>{{ toolCall.output }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, defineProps, defineEmits, computed } from 'vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  toolCalls: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['update:modelValue']);

const isVisible = ref(props.modelValue);

// 处理工具调用数据，将其转换为适合展示的格式
const processedToolCalls = computed(() => {
  if (!props.toolCalls || props.toolCalls.length === 0) return [];
  
  // 如果toolCalls是字符串，尝试解析为JSON
  let toolCallsData = props.toolCalls;
  if (typeof toolCallsData === 'string') {
    try {
      toolCallsData = JSON.parse(toolCallsData);
    } catch (e) {
      console.error('解析工具调用数据失败:', e);
      return [];
    }
  }
  
  // 如果toolCallsData是一个对象，将其转换为数组
  if (!Array.isArray(toolCallsData)) {
    toolCallsData = [toolCallsData];
  }
  
  // 处理每个工具调用
  return toolCallsData.map((toolCall, index) => {
    // 如果工具调用是字符串，尝试解析为JSON
    if (typeof toolCall === 'string') {
      try {
        toolCall = JSON.parse(toolCall);
      } catch (e) {
        console.error('解析单个工具调用失败:', e);
        return {
          name: '未知工具',
          input: '',
          output: toolCall,
          status: 'unknown'
        };
      }
    }
    
    // 如果工具调用是对象，提取相关信息
    if (typeof toolCall === 'object' && toolCall !== null) {
      return {
        name: toolCall.name || toolCall.tool || `工具${index + 1}`,
        input: toolCall.input ? 
               (typeof toolCall.input === 'string' ? toolCall.input : JSON.stringify(toolCall.input, null, 2)) : 
               (toolCall.query || ''),
        output: toolCall.output ? 
                (typeof toolCall.output === 'string' ? toolCall.output : JSON.stringify(toolCall.output, null, 2)) : 
                (toolCall.result || toolCall.response || ''),
        status: toolCall.status || 'success'
      };
    }
    
    // 其他情况，将整个对象作为输出
    return {
      name: `工具${index + 1}`,
      input: '',
      output: typeof toolCall === 'string' ? toolCall : JSON.stringify(toolCall, null, 2),
      status: 'unknown'
    };
  });
});

const handleClose = () => {
  isVisible.value = false;
  emit('update:modelValue', false);
};

const getToolTagType = (status) => {
  switch (status) {
    case 'success':
      return 'success';
    case 'error':
      return 'danger';
    case 'pending':
      return 'warning';
    default:
      return 'info';
  }
};
</script>

<style scoped>
.tool-drawer-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tool-calls-list {
  flex: 1;
  overflow-y: auto;
}

.tool-call-item {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background-color: var(--el-bg-color-overlay);
}

.tool-call-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.tool-name {
  font-weight: bold;
  font-size: 16px;
}

.tool-call-details {
  margin-left: 10px;
}

.tool-call-details h4 {
  margin: 10px 0 5px 0;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.tool-call-details pre {
  background-color: var(--el-bg-color-page);
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.4;
  margin: 0;
}
</style>