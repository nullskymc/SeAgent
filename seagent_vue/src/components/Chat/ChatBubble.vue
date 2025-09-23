<template>
  <div class="message-bubble" :class="message.role">
    <div class="avatar">
      <img v-if="message.role === 'model'" src="@/assets/logo.svg" alt="AI">
      <el-icon v-else-if="message.role === 'user'">
        <UserFilled />
      </el-icon>
    </div>
    <div class="content">
      <!-- User message header with actions -->
      <div class="message-header" v-if="message.role === 'user'">
        <div class="message-actions">
          <el-button
            class="action-btn edit-btn"
            size="small"
            @click.stop="toggleEdit"
          >
            <el-icon><Edit /></el-icon>
          </el-button>
          <el-button
            class="action-btn retry-btn"
            size="small"
            @click.stop="handleRetry"
            :loading="retrying"
          >
            <el-icon><Refresh /></el-icon>
          </el-button>
          <el-button
            class="action-btn delete-btn"
            size="small"
            @click.stop="handleDelete"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- AI message header with retry action only -->
      <div class="message-header" v-else-if="message.role === 'model'">
        <div class="message-actions">
          <el-button
            class="action-btn retry-btn"
            size="small"
            @click.stop="handleRetry"
            :loading="retrying"
          >
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- Message content -->
      <div v-if="isEditing" class="edit-content">
        <el-input
          v-model="editedMessage"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 6 }"
          class="edit-input"
        />
        <div class="edit-actions">
          <el-button size="small" @click="cancelEdit">取消</el-button>
          <el-button type="primary" size="small" @click="saveEdit">保存</el-button>
        </div>
      </div>
      <div v-else-if="message.role === 'model' && !isEditing" class="text markdown-body" v-html="parseMarkdown(message.message)"></div>
      <div v-else class="text">{{ message.message }}</div>

      <!-- Typing indicator -->
      <div v-if="message.isTyping" class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>

      <div class="timestamp">{{ formatTime(message.timestamp) }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits } from 'vue';
import { UserFilled, Edit, Delete, Refresh } from '@element-plus/icons-vue';
import dayjs from 'dayjs';

const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  parseMarkdown: {
    type: Function,
    required: true
  },
  formatTime: {
    type: Function,
    required: true
  }
});

const emit = defineEmits(['delete', 'edit', 'retry']);

// Editing state
const isEditing = ref(false);
const editedMessage = ref(props.message.message);
const retrying = ref(false);

// Toggle edit mode
const toggleEdit = () => {
  isEditing.value = !isEditing.value;
  editedMessage.value = props.message.message;
};

// Cancel editing
const cancelEdit = () => {
  isEditing.value = false;
  editedMessage.value = props.message.message;
};

// Save edited message
const saveEdit = () => {
  if (editedMessage.value.trim()) {
    emit('edit', props.message, editedMessage.value.trim());
    isEditing.value = false;
  }
};

// Handle delete
const handleDelete = () => {
  emit('delete', props.message);
};

// Handle retry for AI messages
const handleRetry = async () => {
  retrying.value = true;
  try {
    await emit('retry', props.message);
  } finally {
    retrying.value = false;
  }
};
</script>

<style scoped>
.message-bubble {
  display: flex;
  max-width: 85%;
  margin-bottom: 20px;
  position: relative;
  opacity: 1;
  animation: fadeIn 0.3s ease-out;
}

.message-bubble.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.message-bubble.user .avatar {
  align-self: flex-end;
}

.message-bubble.user .content {
  align-items: flex-end;
  background: var(--el-color-primary);
  color: white;
  border-bottom-right-radius: 4px;
  border-top-right-radius: 16px;
  border-top-left-radius: 16px;
  border-bottom-left-radius: 16px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.message-bubble.user .content:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.message-bubble.model .avatar {
  align-self: flex-end;
}

.message-bubble.model .content {
  border-bottom-left-radius: 4px;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  border-bottom-right-radius: 16px;
  background: var(--el-bg-color-overlay);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--el-border-color-light);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.message-bubble.model .content:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  border-color: var(--el-border-color-base);
}

.avatar {
  width: 36px;
  height: 36px;
  margin: 0 12px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar img {
  width: 100%;
  border-radius: 50%;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.avatar .el-icon {
  font-size: 24px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  border-radius: 50%;
  padding: 6px;
}

.content {
  padding: 16px;
  border-radius: 16px;
  max-width: 100%;
  position: relative;
  transition: all 0.2s ease;
}

.message-header {
  position: relative;
  height: 0;
}

.message-actions {
  position: absolute;
  top: -12px;
  right: -12px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: all 0.2s ease;
  transform: scale(0.9);
}

.message-bubble:hover .message-actions {
  opacity: 1;
  transform: scale(1);
}

.action-btn {
  width: 24px;
  height: 24px;
  padding: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-btn {
  background: var(--el-color-warning-light-9);
  border-color: var(--el-color-warning-light-5);
  color: var(--el-color-warning);
}

.delete-btn {
  background: var(--el-color-danger-light-9);
  border-color: var(--el-color-danger-light-5);
  color: var(--el-color-danger);
}

.retry-btn {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-5);
  color: var(--el-color-primary);
}

.edit-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.edit-input :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.1);
  border-color: var(--el-border-color-light);
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.text {
  line-height: 1.6;
  white-space: pre-wrap;
  font-size: 15px;
}

/* Markdown样式 */
.markdown-body {
  white-space: normal;

  /* KaTeX 数学公式样式 */
  :deep(.katex-block) {
    display: block;
    margin: 1em 0;
    text-align: center;
    overflow-x: auto;
    overflow-y: hidden;
  }

  :deep(.katex) {
    font-size: 1.1em;
    line-height: 1.2;
    text-indent: 0;
  }

  :deep(.katex-display) {
    margin: 0.5em 0;
    overflow-x: auto;
    overflow-y: hidden;
  }

  :deep(pre) {
    background-color: #282c34;
    border-radius: 4px;
    padding: 12px;
    overflow-x: auto;
    margin: 8px 0;
  }

  :deep(code) {
    font-family: 'Courier New', Courier, monospace;
    padding: 2px 4px;
    background-color: rgba(0, 0, 0, 0.06);
    border-radius: 3px;
  }

  :deep(pre code) {
    background-color: transparent;
    padding: 0;
  }

  :deep(blockquote) {
    border-left: 4px solid #ddd;
    padding: 0 15px;
    color: #777;
    margin: 10px 0;
  }

  :deep(table) {
    border-collapse: collapse;
    margin: 12px 0;
    width: 100%;
  }

  :deep(th), :deep(td) {
    border: 1px solid #ddd;
    padding: 8px 12px;
    text-align: left;
  }

  :deep(th) {
    background-color: #f2f2f2;
  }

  :deep(img) {
    max-width: 100%;
    border-radius: 4px;
  }

  :deep(p) {
    margin: 6px 0; /* 减少段落间距 */
  }

  :deep(p:first-child) {
    margin-top: 0; /* 移除第一个段落的上边距 */
  }

  :deep(p:last-child) {
    margin-bottom: 0; /* 移除最后一个段落的下边距 */
  }

  :deep(p:empty) {
    display: none; /* 隐藏空段落 */
  }

  :deep(ul), :deep(ol) {
    padding-left: 20px;
    margin: 6px 0; /* 减少列表间距 */
  }

  :deep(ul:first-child), :deep(ol:first-child) {
    margin-top: 0; /* 移除第一个列表的上边距 */
  }

  :deep(ul:last-child), :deep(ol:last-child) {
    margin-bottom: 0; /* 移除最后一个列表的下边距 */
  }

  :deep(li) {
    margin: 4px 0; /* 减少列表项间距 */
  }

  :deep(a) {
    color: var(--el-color-primary);
    text-decoration: none;
  }

  :deep(a:hover) {
    text-decoration: underline;
  }

  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin: 12px 0 6px; /* 减少标题间距 */
    font-weight: 600;
  }

  :deep(h1:first-child), :deep(h2:first-child), :deep(h3:first-child), :deep(h4:first-child), :deep(h5:first-child), :deep(h6:first-child) {
    margin-top: 0; /* 移除第一个标题的上边距 */
  }

  :deep(h1:last-child), :deep(h2:last-child), :deep(h3:last-child), :deep(h4:last-child), :deep(h5:last-child), :deep(h6:last-child) {
    margin-bottom: 0; /* 移除最后一个标题的下边距 */
  }

  /* 移除多余的空行 */
  :deep(br) {
    display: none;
  }

  /* 代码块后的间距 */
  :deep(pre + p) {
    margin-top: 8px;
  }

  /* 表格后的间距 */
  :deep(table + p) {
    margin-top: 12px;
  }
}

.timestamp {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-top: 8px;
  text-align: right;
}

.typing-indicator {
  display: flex;
  align-items: center;
  height: 20px;
  margin-top: 8px;
}

.typing-indicator span {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--el-color-primary);
  margin-right: 4px;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-5px);
  }
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
:root.dark .message-bubble.model .content,
html.dark .message-bubble.model .content,
.el-html--dark .message-bubble.model .content {
  background: var(--el-bg-color-overlay);
  border-color: var(--el-border-color-base);

  /* Markdown暗黑模式样式调整 */
  .markdown-body {
    :deep(code) {
      background-color: rgba(255, 255, 255, 0.1);
    }

    :deep(blockquote) {
      border-left-color: #444;
      color: #aaa;
    }

    :deep(th), :deep(td) {
      border-color: #444;
    }

    :deep(th) {
      background-color: #333;
    }

    :deep(pre) {
      background-color: #1a1a1a;
    }

    :deep(table) {
      border-color: #444;
    }
  }
}

:root.dark .message-bubble.user .content,
html.dark .message-bubble.user .content,
.el-html--dark .message-bubble.user .content {
  background: var(--el-color-primary);
}

:root.dark .message-bubble .avatar .el-icon,
html.dark .message-bubble .avatar .el-icon,
.el-html--dark .message-bubble .avatar .el-icon {
  background: var(--el-color-primary-light-8);
}

/* Responsive design */
@media (max-width: 768px) {
  .message-bubble {
    max-width: 95%;
  }

  .content {
    padding: 12px 14px;
  }
}

@media (max-width: 480px) {
  .message-bubble {
    max-width: 98%;
  }

  .avatar {
    width: 32px;
    height: 32px;
    margin: 0 8px;
  }

  .content {
    padding: 10px 12px;
    font-size: 14px;
  }

  .timestamp {
    font-size: 10px;
  }
}
</style>