<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="header-left">
        <h2>{{ chatTitle }}</h2>
      </div>
      <div class="header-right">
        <el-tooltip content="选择知识库" placement="top">
          <el-button :icon="Reading" circle @click="isKnowledgeDrawerVisible = true"></el-button>
        </el-tooltip>
      </div>
    </div>

    <el-scrollbar class="message-container" ref="messageContainer">
      <!-- 知识库应用提示 -->
      <div v-if="selectedCollection" class="knowledge-info">
        <el-alert type="info" :closable="false" show-icon>
          <template #title>
            <span>当前使用知识库: <strong>{{ selectedCollection }}</strong></span>
          </template>
        </el-alert>
      </div>

      <div v-if="loading" class="loading-indicator">
        <el-icon class="is-loading">
          <Loading />
        </el-icon>
        <span>加载中...</span>
      </div>
      <div v-else-if="messages.length === 0" class="empty-container">
        <el-empty description="暂无消息，发送一条消息开始对话吧" />
      </div>
      <div v-else v-for="(message, index) in messages" :key="index" class="message-bubble" :class="message.role">
        <div class="avatar">
          <img v-if="message.role === 'model'" src="@/assets/logo.svg" alt="AI">
          <el-icon v-else-if="message.role === 'user'">
            <UserFilled />
          </el-icon>
        </div>
        <div class="content">
          <div class="message-header" v-if="message.role === 'user'">
            <el-button class="delete-btn" type="danger" size="small" icon="Delete" circle
              @click.stop="confirmDeleteMessage(message)"></el-button>
          </div>
          <div v-if="message.role === 'model'" class="text markdown-body" v-html="parseMarkdown(message.message)"></div>
          <div v-else class="text">{{ message.message }}</div>
          <div class="timestamp">{{ formatTime(message.timestamp) }}</div>
        </div>
      </div>
      <div v-if="sending" class="loading-indicator">
        <el-icon class="is-loading">
          <Loading />
        </el-icon>
      </div>
    </el-scrollbar>

    <div class="input-area">
      <ChatInput 
        v-model="inputMessage" 
        @send="sendMessage" 
        :loading="sending"
        :disabled="!currentChatId"
      />
    </div>

    <!-- 知识库选择抽屉 -->
    <el-drawer v-model="isKnowledgeDrawerVisible" title="知识库" direction="rtl" size="300px">
      <div class="knowledge-drawer-content">
        <p>选择一个知识库，AI将参考其内容进行回答。</p>
        <KnowledgeSelector @collection-change="handleCollectionChange" />
      </div>
    </el-drawer>

    <!-- 删除消息确认对话框 -->
    <el-dialog v-model="deleteMessageDialogVisible" title="确认删除" width="30%" :close-on-click-modal="false">
      <span>确定要删除这条消息吗？此操作不可恢复。</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteMessageDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="handleDeleteMessage" :loading="deleting">删除</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, defineProps, watch, nextTick } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { UserFilled, Loading, Delete, Reading, Promotion } from '@element-plus/icons-vue';
import dayjs from 'dayjs';
import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { sendMessage as apiSendMessage, getChatMessages, getChatDetail, deleteMessage } from '@/services/chatService';
import { getUserInfo } from '@/services/auth';
import KnowledgeSelector from '@/components/Knowledge/KnowledgeSelector.vue';
import ChatInput from './ChatInput.vue';

const props = defineProps({
  currentChatId: Number
});

const emit = defineEmits(['title-updated']);

// 消息列表和输入消息
const messages = ref([]);
const inputMessage = ref('');
const loading = ref(false); // 加载历史消息状态
const sending = ref(false); // 发送消息状态
const messageContainer = ref(null);
const userId = ref(null);
const chatTitle = ref('新对话');
const chatDetail = ref(null);

// 知识库选择
const selectedCollection = ref('');
const isKnowledgeDrawerVisible = ref(false);

// 删除消息相关状态
const deleteMessageDialogVisible = ref(false);
const messageToDelete = ref(null);
const deleting = ref(false);

// 获取用户ID
const userInfo = getUserInfo();
if (userInfo) {
  userId.value = userInfo.id;
}

// 格式化时间
const formatTime = (date) => {
  if (!date) return '';
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
};

// Markdown解析函数
const parseMarkdown = (text) => {
  if (!text) return '';
  try {
    // 首先处理数学公式
    let processedText = text;
    
    // 处理行内公式 $...$ 
    processedText = processedText.replace(/\$([^\$]+)\$/g, (match, formula) => {
      try {
        return katex.renderToString(formula, {
          throwOnError: false,
          displayMode: false
        });
      } catch (err) {
        console.error('KaTeX行内公式解析错误:', err);
        return match; // 出错时保留原文
      }
    });
    
    // 处理块级公式 $...$
    processedText = processedText.replace(/\$\$([^\$]+)\$\$/g, (match, formula) => {
      try {
        return `<div class="katex-block">${katex.renderToString(formula, {
          throwOnError: false,
          displayMode: true
        })}</div>`;
      } catch (err) {
        console.error('KaTeX块级公式解析错误:', err);
        return match; // 出错时保留原文
      }
    });
    
    // 然后应用 Markdown 解析
    return marked(processedText);
  } catch (error) {
    console.error('Markdown解析错误:', error);
    return text; // 解析失败，返回原文本
  }
};

// 处理知识库选择变化
const handleCollectionChange = (collection) => {
  selectedCollection.value = collection;
  if (collection) {
    ElMessage.success(`已选择知识库: ${collection}`);
  }
  isKnowledgeDrawerVisible.value = false; // 关闭抽屉
};

// 获取对话消息
const fetchChatMessages = async (chatId) => {
  if (!chatId) return;

  loading.value = true;
  messages.value = []; // 清空现有消息

  try {
    // 获取对话详情
    const detailResponse = await getChatDetail(chatId);
    chatDetail.value = detailResponse.chat;
    chatTitle.value = chatDetail.value.title;

    // 获取消息列表，按时间升序排列
    const messagesResponse = await getChatMessages(chatId);
    messages.value = messagesResponse;

    // 如果没有消息，显示欢迎消息
    if (messages.value.length === 0) {
      messages.value = [{
        role: 'model',
        message: '您好！我是智能助手，请问有什么可以帮您？',
        timestamp: new Date().toISOString()
      }];
    }

    await nextTick();
    scrollToBottom();
  } catch (error) {
    console.error('获取对话消息失败:', error);
    ElMessage.error('获取对话消息失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || sending.value || !props.currentChatId) return;
  if (!userId.value) {
    ElMessage.warning('请先登录');
    return;
  }

  const isNewChat = chatTitle.value === '新对话';

  // 用户消息
  const userMsg = {
    role: 'user',
    message: inputMessage.value.trim(),
    timestamp: new Date().toISOString()
  };
  messages.value.push(userMsg);

  // 清空输入框
  const userInput = inputMessage.value.trim();
  inputMessage.value = '';

  // 滚动到底部
  await nextTick();
  scrollToBottom();

  // 发送消息到API，包含知识库选择
  sending.value = true;
  try {
    const response = await apiSendMessage(
      props.currentChatId,
      userId.value,
      userInput,
      'user',
      selectedCollection.value || null
    );

    // 添加AI回复
    if (response) {
      messages.value.push({
        role: 'model',
        message: response.message,
        timestamp: response.timestamp
      });

      // 再次滚动到底部
      await nextTick();
      scrollToBottom();

      // 如果是新对话的第一次问答，则生成标题
      if (isNewChat && messages.value.length === 2) {
        try {
          const titleResponse = await generateChatTitle(props.currentChatId);
          if (titleResponse && titleResponse.title) {
            chatTitle.value = titleResponse.title;
            emit('title-updated');
          }
        } catch (titleError) {
          console.error('自动生成标题失败:', titleError);
        }
      }
    }
  } catch (error) {
    console.error('发送消息失败:', error);
    ElMessage.error('发送消息失败，请稍后重试');
  } finally {
    sending.value = false;
  }
};

// 确认删除消息
const confirmDeleteMessage = (message) => {
  if (message.role === 'user') {
    messageToDelete.value = message;
    deleteMessageDialogVisible.value = true;
  }
};

// 执行删除消息
const handleDeleteMessage = async () => {
  if (!messageToDelete.value || !messageToDelete.value.id) {
    ElMessage.warning('无法删除此消息');
    deleteMessageDialogVisible.value = false;
    return;
  }

  deleting.value = true;
  try {
    await deleteMessage(messageToDelete.value.id);

    // 从消息列表中移除已删除的消息
    messages.value = messages.value.filter(msg => msg.id !== messageToDelete.value.id);

    ElMessage.success('消息已删除');
    deleteMessageDialogVisible.value = false;
  } catch (error) {
    console.error('删除消息失败:', error);
    ElMessage.error('删除消息失败，请稍后重试');
  } finally {
    deleting.value = false;
  }
};

// 滚动到底部
const scrollToBottom = () => {
  if (messageContainer.value) {
    const scrollbar = messageContainer.value;
    scrollbar.setScrollTop(scrollbar.wrapRef.scrollHeight);
  }
};

// 监听聊天ID变化，加载历史消息
watch(() => props.currentChatId, async (newChatId) => {
  if (newChatId) {
    // 加载指定对话的历史消息
    await fetchChatMessages(newChatId);
  } else {
    // 没有选中对话，显示提示
    messages.value = [];
    chatTitle.value = '请选择对话';
  }
}, { immediate: true });
</script>

<style scoped>
.chat-main {
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
}

.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid var(--el-border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;

  h2 {
    margin: 0;
    font-size: 18px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.knowledge-drawer-content {
  padding: 0 20px;
}

.message-container {
  flex: 1;
  width: 100%;
  min-height: 0;
  /* 关键：允许内容区域收缩 */
  overflow-y: auto;
  padding: 24px;
  transition: margin-left 0.3s ease;
}

.knowledge-info {
  margin-bottom: 20px;
}

.knowledge-tip {
  font-size: 12px;
  margin: 4px 0 0 0;
}

.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 20px 0;
  font-size: 16px;
  color: var(--el-color-primary);
  gap: 10px;
}

.empty-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.message-bubble {
  display: flex;
  max-width: 90%;
  margin-bottom: 24px;
  position: relative;

  &.user {
    flex-direction: row-reverse;
    margin-left: auto;

    .content {
      align-items: flex-end;
      background: var(--el-color-primary);
      color: white;
    }

    .delete-btn {
      position: absolute;
      top: -10px;
      right: -10px;
      opacity: 0;
      transition: opacity 0.3s ease;
    }

    &:hover .delete-btn {
      opacity: 1;
    }
  }

  .avatar {
    width: 32px;
    height: 32px;
    margin: 0 12px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;

    img {
      width: 100%;
      border-radius: 4px;
    }

    .el-icon {
      font-size: 28px;
      color: var(--el-color-primary);
    }
  }

  .content {
    padding: 12px 16px;
    border-radius: 8px;
    background: var(--el-bg-color);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    max-width: 1200px;
    position: relative;

    .message-header {
      position: relative;
      height: 0;
    }

    .text {
      line-height: 1.6;
      white-space: pre-wrap;
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
        margin: 8px 0;
      }

      :deep(ul), :deep(ol) {
        padding-left: 20px;
      }

      :deep(a) {
        color: var(--el-color-primary);
        text-decoration: none;
      }

      :deep(a:hover) {
        text-decoration: underline;
      }

      :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
        margin: 16px 0 8px;
        font-weight: 600;
      }
    }

    .timestamp {
      font-size: 12px;
      color: var(--el-text-color-placeholder);
      margin-top: 8px;
    }
  }
}


/* 暗黑模式适配 */
:root.dark .message-bubble .content,
html.dark .message-bubble .content,
.el-html--dark .message-bubble .content {
  background: var(--el-bg-color-overlay);

  /* 暗黑模式的Markdown样式调整 */
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
  }
}

:root.dark .message-bubble.user .content,
html.dark .message-bubble.user .content,
.el-html--dark .message-bubble.user .content {
  background: var(--el-color-primary);
}

:root.dark .input-area :deep(.el-textarea__inner) {
  background-color: #2c2c2f;
  border-color: #4a4a4f;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
</style>
