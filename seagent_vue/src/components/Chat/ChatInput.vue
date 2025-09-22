<template>
  <div class="chat-input-bar-wrapper">
    <el-input
      v-model="message"
      type="textarea"
      :autosize="{ minRows: 1, maxRows: 5 }"
      placeholder="输入消息... (Ctrl+Enter 发送)"
      @keyup.enter.ctrl.exact="handleSend"
      class="chat-input-textarea"
      resize="none"
    />
    <el-button
      class="send-button"
      type="primary"
      circle
      :icon="Promotion"
      @click="handleSend"
      :loading="loading"
      :disabled="isButtonDisabled"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Promotion } from '@element-plus/icons-vue';

const props = defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:modelValue', 'send']);

const message = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

const isButtonDisabled = computed(() => {
  return props.disabled || !props.modelValue.trim();
});

const handleSend = () => {
  if (!isButtonDisabled.value) {
    emit('send');
  }
};
</script>

<style scoped>
.chat-input-bar-wrapper {
  display: flex;
  align-items: flex-end; /* 关键：使按钮和多行文本域底部对齐 */
  padding: 8px 12px;
  background: var(--el-bg-color);
  border-radius: 22px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--el-border-color-lighter);
  transition: all 0.2s ease-in-out;
}

.chat-input-bar-wrapper:focus-within {
  border-color: var(--el-color-primary);
  box-shadow: 0 4px 16px rgba(var(--el-color-primary-rgb), 0.2);
}

.chat-input-textarea {
  flex: 1;
  margin: 0 8px;
}

/* 穿透el-input样式，使其与容器融合 */
:deep(.el-textarea__inner) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 6px 0 !important;
  line-height: 1.6;
}

.send-button {
  flex-shrink: 0;
}

/* 暗黑模式适配 */
:root.dark .chat-input-bar-wrapper,
html.dark .chat-input-bar-wrapper,
.el-html--dark .chat-input-bar-wrapper {
  background-color: #2c2c2f;
  border-color: #4a4a4f;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
</style>
