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
      <template v-for="(message, index) in messages" :key="index">
        <!-- 普通聊天消息 -->
        <ChatBubble
          v-if="message.role === 'user' || message.role === 'model'"
          :message="message"
          :parse-markdown="parseMarkdown"
          :format-time="formatTime"
          @delete="confirmDeleteMessage"
          @edit="handleEditMessage"
          @retry="handleRetryMessage"
        />
        <!-- 工具调用消息 -->
        <ToolCallBubble
          v-else-if="message.role === 'tool'"
          :tool-call="message"
        />
      </template>
      <div v-if="sending" class="loading-indicator">
        <el-icon class="is-loading">
          <Loading />
        </el-icon>
        <span>AI正在思考中...</span>
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
import { UserFilled, Loading, Delete, Reading, Promotion, Edit, Refresh, Tools } from '@element-plus/icons-vue';
import dayjs from 'dayjs';
import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';

// Configure marked to minimize extra line breaks
marked.setOptions({
  breaks: false,
  gfm: true,
  headerIds: false
});
import { sendMessage as apiSendMessage, sendStreamMessage, getChatMessages, getChatDetail, deleteMessage, updateMessage, generateChatTitle } from '@/services/chatService';
import { getUserInfo } from '@/services/auth';
import KnowledgeSelector from '@/components/Knowledge/KnowledgeSelector.vue';
import ChatInput from './ChatInput.vue';
import ChatBubble from './ChatBubble.vue';
import ToolCallBubble from './ToolCallBubble.vue';

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
    
    // 处理消息，确保工具消息正确转换
    const processedMessages = messagesResponse.map(msg => {
      if (msg.role === 'tool') {
        // 确保工具消息有正确的字段
        return {
          ...msg,
          name: msg.tool_name || msg.name,
          input: msg.tool_input || msg.input,
          output: msg.tool_output || msg.output,
          status: msg.tool_status || msg.status,
          isToolCall: true
        };
      }
      return msg;
    });
    
    messages.value = processedMessages;
    
    console.log('📋 加载的消息:', messages.value); // 调试日志

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

  const userInput = inputMessage.value.trim();
  const isNewChat = chatTitle.value === '新对话';

  // 1. Add user message to UI
  messages.value.push({
    role: 'user',
    message: userInput,
    timestamp: new Date().toISOString()
  });
  inputMessage.value = '';
  await nextTick();
  scrollToBottom();

  // 2. Execute the stream sending logic
  await executeStream(userInput, isNewChat);
};

// Centralized stream execution logic
const executeStream = async (messageContent, isNewChat = false) => {
  sending.value = true;

  // 1. Add a blank AI message placeholder to the UI
  const aiMessage = {
    role: 'model',
    message: '',
    tool_calls: [],
    timestamp: new Date().toISOString(),
    isTyping: true,
    id: `ai_${Date.now()}` // 添加唯一ID来跟踪AI消息
  };
  messages.value.push(aiMessage);
  await nextTick();
  scrollToBottom();

  // 2. Call the refactored service with enhanced callbacks
  try {
    await sendStreamMessage(
      {
        chatId: props.currentChatId,
        userId: userId.value,
        message: messageContent,
        role: 'user',
        collection_name: selectedCollection.value || null,
      },
      {
        onMessage: (content) => {
          // 实时更新AI消息内容，通过ID查找确保准确性
          const currentAiMessage = messages.value.find(msg => msg.id === aiMessage.id);
          if (currentAiMessage) {
            currentAiMessage.message += content;
            // 保持isTyping状态为true，让ChatBubble组件自动处理打字机效果
          }
        },
        onToolCall: async (dataString) => {
          console.log('🔧 收到工具调用数据:', dataString); // 调试日志
          
          // 处理工具调用，将其作为独立的消息添加到聊天中
          try {
            if (dataString.startsWith('[TOOL_CALL_START]')) {
              // 更安全的JSON数据提取
              let jsonData = '';
              if (dataString.endsWith('[TOOL_CALL_END]')) {
                jsonData = dataString.slice('[TOOL_CALL_START]'.length, -'[TOOL_CALL_END]'.length);
              } else {
                // 如果没有结束标记，提取从开始标记到字符串结尾的内容
                jsonData = dataString.slice('[TOOL_CALL_START]'.length);
              }
              
              console.log('🔍 提取的JSON数据:', jsonData); // 调试日志
              const toolData = JSON.parse(jsonData);
              
              // UTF解码函数
              const decodeUTF = (str) => {
                if (typeof str === 'string') {
                  try {
                    // 解码 \uXXXX 格式的Unicode字符
                    return str.replace(/\\u[\dA-Fa-f]{4}/g, (match) => {
                      return String.fromCharCode(parseInt(match.replace(/\\u/g, ''), 16));
                    });
                  } catch (e) {
                    return str;
                  }
                } else if (typeof str === 'object') {
                  // 递归解码对象中的UTF字符
                  const decoded = {};
                  for (const [key, value] of Object.entries(str)) {
                    decoded[decodeUTF(key)] = decodeUTF(value);
                  }
                  return decoded;
                }
                return str;
              };
              
              // 解码工具调用数据
              const decodedToolData = {
                name: decodeUTF(toolData.name),
                input: decodeUTF(toolData.input),
                status: toolData.status || 'started'
              };
              
              // 创建工具调用消息 - 确保添加到消息列表
              const toolCallMessage = {
                id: Date.now(), // 临时ID
                role: 'tool',
                name: decodedToolData.name,
                input: decodedToolData.input,
                output: '', // 初始为空，等待结果
                status: decodedToolData.status,
                timestamp: new Date().toISOString(),
                isToolCall: true,
                message: `工具调用: ${decodedToolData.name}`, // 用于显示的消息文本
                // 工具调用特有的字段
                tool_name: decodedToolData.name,
                tool_input: decodedToolData.input,
                tool_output: '',
                tool_status: decodedToolData.status
              };
              
              console.log('➕ 添加工具消息到界面:', toolCallMessage); // 调试日志
              
              // 添加到消息列表 - 添加到AI消息之后（正确的时序）
              messages.value.push(toolCallMessage);
              await nextTick();
              scrollToBottom();
              
            } else if (dataString.startsWith('[TOOL_RESULT_START]')) {
              // 更安全的JSON数据提取
              let jsonData = '';
              if (dataString.endsWith('[TOOL_RESULT_END]')) {
                jsonData = dataString.slice('[TOOL_RESULT_START]'.length, -'[TOOL_RESULT_END]'.length);
              } else {
                // 如果没有结束标记，提取从开始标记到字符串结尾的内容
                jsonData = dataString.slice('[TOOL_RESULT_START]'.length);
              }
              
              console.log('🔍 提取的工具结果JSON数据:', jsonData); // 调试日志
              const resultData = JSON.parse(jsonData);
              
              // UTF解码函数
              const decodeUTF = (str) => {
                if (typeof str === 'string') {
                  try {
                    return str.replace(/\\u[\dA-Fa-f]{4}/g, (match) => {
                      return String.fromCharCode(parseInt(match.replace(/\\u/g, ''), 16));
                    });
                  } catch (e) {
                    return str;
                  }
                }
                return str;
              };
              
              // 查找对应的工具调用消息并更新结果
              const toolName = decodeUTF(resultData.name);
              const toolMessage = messages.value.slice().reverse().find(msg => 
                msg.role === 'tool' && 
                msg.name === toolName &&
                !msg.output // 找到还没有输出结果的工具消息
              );
              
              if (toolMessage) {
                const decodedOutput = decodeUTF(resultData.output);
                toolMessage.output = decodedOutput;
                toolMessage.tool_output = decodedOutput;
                toolMessage.status = 'completed';
                toolMessage.tool_status = 'completed';
                // 更新消息文本以包含结果
                toolMessage.message = `工具调用: ${toolMessage.name} - 已完成`;
                
                console.log('✅ 更新工具消息结果:', { toolName, output: decodedOutput.substring(0, 100) }); // 调试日志
                
                await nextTick();
                scrollToBottom();
              } else {
                console.warn('⚠️ 未找到对应的工具消息:', toolName);
              }
              
            } else if (dataString.startsWith('[TOOL_SUMMARY_START]')) {
              // 忽略工具总结，因为我们已经单独显示了每个工具调用
              console.log('🙈 忽略工具总结:', dataString.substring(0, 100));
              return;
            }
          } catch (e) {
            console.error('❌ 解析工具调用数据失败:', e, dataString);
          }
          
          // 同时保持原有的AI消息中的工具调用记录（用于工具抽屉显示）
          const currentAiMessage = messages.value.find(msg => msg.id === aiMessage.id);
          if (currentAiMessage) {
            if (!currentAiMessage.tool_calls) {
              currentAiMessage.tool_calls = [];
            }
            
            try {
              if (dataString.startsWith('[TOOL_CALL_START]')) {
                let jsonData = '';
                if (dataString.endsWith('[TOOL_CALL_END]')) {
                  jsonData = dataString.slice('[TOOL_CALL_START]'.length, -'[TOOL_CALL_END]'.length);
                } else {
                  jsonData = dataString.slice('[TOOL_CALL_START]'.length);
                }
                const toolData = JSON.parse(jsonData);
                currentAiMessage.tool_calls.push({
                  name: toolData.name,
                  input: toolData.input,
                  status: 'pending'
                });
              } else if (dataString.startsWith('[TOOL_RESULT_START]')) {
                let jsonData = '';
                if (dataString.endsWith('[TOOL_RESULT_END]')) {
                  jsonData = dataString.slice('[TOOL_RESULT_START]'.length, -'[TOOL_RESULT_END]'.length);
                } else {
                  jsonData = dataString.slice('[TOOL_RESULT_START]'.length);
                }
                const resultData = JSON.parse(jsonData);
                const toolCall = currentAiMessage.tool_calls.find(tc => 
                  tc.name === resultData.name && 
                  JSON.stringify(tc.input) === JSON.stringify(resultData.input)
                );
                if (toolCall) {
                  toolCall.output = resultData.output;
                  toolCall.status = 'success';
                }
              }
            } catch (e) {
              console.error('更新AI消息工具调用记录失败:', e);
            }
          }
        },
        onTyping: (isTypingActive) => {
          // 控制打字机效果状态
          const currentAiMessage = messages.value.find(msg => msg.id === aiMessage.id);
          if (currentAiMessage) {
            currentAiMessage.isTyping = isTypingActive;
          }
        },
        onDone: async (fullResponse) => {
          const currentAiMessage = messages.value.find(msg => msg.id === aiMessage.id);
          if (currentAiMessage) {
            // 确保显示完整响应并停止打字机效果
            currentAiMessage.isTyping = false;
            currentAiMessage.message = fullResponse;
            await nextTick();
            scrollToBottom();
          }
          
          // Generate title for the first message in a new chat
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
        },
        onError: (error) => {
          console.error('流式响应错误:', error);
          const currentAiMessage = messages.value.find(msg => msg.id === aiMessage.id);
          if (currentAiMessage) {
            currentAiMessage.isTyping = false;
            currentAiMessage.message = `抱歉，处理请求时出错: ${error.message}`;
          }
        },
      }
    );
  } catch (error) {
    console.error('发送消息失败:', error);
    ElMessage.error('发送消息失败，请稍后重试');
    // 发生灾难性故障时删除AI消息占位符
    const aiMessageIndex = messages.value.findIndex(msg => msg.id === aiMessage.id);
    if (aiMessageIndex !== -1) {
      messages.value.splice(aiMessageIndex, 1);
    }
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

// 编辑消息
const handleEditMessage = async (message, newContent) => {
  if (!message.id) {
    ElMessage.warning('无法编辑此消息');
    return;
  }

  try {
    await updateMessage(message.id, newContent);
    const messageIndex = messages.value.findIndex(msg => msg.id === message.id);
    if (messageIndex !== -1) {
      messages.value[messageIndex].message = newContent;
      ElMessage.success('消息已更新');
    }
  } catch (error) {
    console.error('编辑消息失败:', error);
    ElMessage.error('编辑消息失败，请稍后重试');
  }
};

// 统一重试消息处理
const handleRetryMessage = async (message) => {
  if (!props.currentChatId || !userId.value) {
    ElMessage.warning('缺少必要信息');
    return;
  }

  const messageIndex = messages.value.findIndex(msg => msg.id === message.id);
  if (messageIndex === -1) {
    ElMessage.warning('未找到要重试的消息');
    return;
  }

  // Find the user message that prompted this response
  let userMessageToRetry = null;
  if (message.role === 'user') {
    userMessageToRetry = message;
    // Remove the user message and all subsequent messages
    messages.value.splice(messageIndex);
  } else if (message.role === 'model' && messageIndex > 0) {
    const prevMessage = messages.value[messageIndex - 1];
    if (prevMessage.role === 'user') {
      userMessageToRetry = prevMessage;
      // Remove the AI message and all subsequent messages
      messages.value.splice(messageIndex);
    }
  }

  if (userMessageToRetry) {
    // Re-add the user message to the list to show it's being processed
    messages.value.push({
      role: 'user',
      message: userMessageToRetry.message,
      timestamp: new Date().toISOString()
    });
    await nextTick();
    scrollToBottom();
    
    // Execute the stream again
    await executeStream(userMessageToRetry.message);
  } else {
    ElMessage.warning('无法找到有效的用户消息进行重试');
  }
};

// 滚动到底部
const scrollToBottom = () => {
  if (messageContainer.value) {
    const scrollbar = messageContainer.value;
    scrollbar.setScrollTop(scrollbar.wrapRef.scrollHeight);
  }
};

// 使用动画显示模型响应
const displayModelResponseWithAnimation = async (messageIndex, content) => {
  console.log('开始动画显示模型响应:', content);
  
  // 设置完整内容并标记为新消息以触发动画
  messages.value[messageIndex].message = content;
  messages.value[messageIndex].isNew = true;
  
  // 触发重新渲染
  await nextTick();
  
  // 滚动到底部
  scrollToBottom();
  
  // 动画完成后移除标记
  setTimeout(() => {
    if (messages.value[messageIndex]) {
      messages.value[messageIndex].isNew = false;
    }
  }, 500);
  
  console.log('模型响应动画显示完成');
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
  background: var(--el-bg-color-page);
}

:root.dark .message-container,
html.dark .message-container,
.el-html--dark .message-container {
  background: var(--el-bg-color);
}

.knowledge-info {
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease-out;
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
  animation: fadeIn 0.3s ease-out;
}

.empty-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  animation: fadeIn 0.5s ease-out;
}

.message-bubble {
  display: flex;
  max-width: 85%;
  margin-bottom: 20px;
  position: relative;
  opacity: 1;
  animation: fadeIn 0.3s ease-out;

  &.user {
    flex-direction: row-reverse;
    margin-left: auto;

    .avatar {
      align-self: flex-end;
    }

    .content {
      align-items: flex-end;
      background: var(--el-color-primary);
      color: white;
      border-bottom-right-radius: 4px;
      border-top-right-radius: 16px;
      border-top-left-radius: 16px;
      border-bottom-left-radius: 16px;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .content:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
    }

    .delete-btn {
      position: absolute;
      top: -12px;
      right: -12px;
      opacity: 0;
      transition: all 0.2s ease;
      transform: scale(0.9);
    }

    &:hover .delete-btn {
      opacity: 1;
      transform: scale(1);
    }
  }

  &.model {
    .avatar {
      align-self: flex-end;
    }

    .content {
      border-bottom-left-radius: 4px;
      border-top-left-radius: 16px;
      border-top-right-radius: 16px;
      border-bottom-right-radius: 16px;
      background: var(--el-bg-color-overlay);
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
      border: 1px solid var(--el-border-color-light);
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .content:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
      border-color: var(--el-border-color-base);
    }
  }

  .avatar {
    width: 36px;
    height: 36px;
    margin: 0 12px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;

    img {
      width: 100%;
      border-radius: 50%;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }

    .el-icon {
      font-size: 24px;
      color: var(--el-color-primary);
      background: var(--el-color-primary-light-9);
      border-radius: 50%;
      padding: 6px;
    }
  }

  .content {
    padding: 16px;
    border-radius: 16px;
    max-width: 100%;
    position: relative;
    transition: all 0.2s ease;

    .message-header {
      position: relative;
      height: 0;
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

    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(10px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }
  }
}


/* 暗黑模式适配 */
:root.dark .message-bubble .content,
html.dark .message-bubble .content,
.el-html--dark .message-bubble .content {
  background: var(--el-bg-color-overlay);
  border-color: var(--el-border-color-base);

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

:root.dark .message-bubble .avatar .el-icon,
html.dark .message-bubble .avatar .el-icon,
.el-html--dark .message-bubble .avatar .el-icon {
  background: var(--el-color-primary-light-8);
}

:root.dark .input-area :deep(.el-textarea__inner) {
  background-color: #2c2c2f;
  border-color: #4a4a4f;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .message-bubble {
    max-width: 95%;
  }

  .message-container {
    padding: 16px;
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
