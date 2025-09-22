<!-- ChatHistory.vue -->
<template>
  <div class="history-sidebar-wrapper">
    <el-aside class="history-sidebar">
      <div class="history-header">
        <h3>对话历史</h3>
        <el-button type="primary" @click="handleCreateChat" plain round :loading="isCreating">
          <el-icon>
            <Plus />
          </el-icon>新对话
        </el-button>
      </div>

      <el-scrollbar class="history-list">
        <div v-if="loading" class="loading-wrapper">
          <el-icon class="is-loading">
            <Loading />
          </el-icon>
          <span>加载中...</span>
        </div>

        <div v-else-if="chatList.length === 0" class="empty-list">
          <el-empty description="暂无对话历史" />
        </div>

        <div v-else v-for="(chat, index) in chatList" :key="chat.id" class="history-item"
          :class="{ active: activeChat === chat.id }">
          <div class="item-content" @click="selectChat(chat.id)">
            <el-icon class="chat-icon">
              <ChatLineRound />
            </el-icon>

            <div class="content-wrapper">
              <div class="title-row">
                <span class="title">{{ chat.title }}</span>
              </div>
              <div class="preview" :title="chat.last_message || '对话已开始'">{{ chat.last_message || '对话已开始' }}</div>
              <div class="time">{{ formatTime(chat.updated_at) }}</div>
            </div>
          </div>

          <!-- 删除按钮 - 仅当悬停时显示 -->
          <div class="action-buttons">
            <el-button class="delete-btn" type="danger" :icon="Delete" circle
              @click.stop="handleDeleteChat(chat)"></el-button>
          </div>
        </div>
      </el-scrollbar>
    </el-aside>

    <!-- 重命名对话对话框 -->
    <el-dialog v-model="renameDialogVisible" title="重命名对话" width="30%">
      <el-input v-model="newChatTitle" placeholder="请输入新标题" />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="renameDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmRenameChat" :loading="isRenaming">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 删除确认对话框 -->
    <el-dialog v-model="deleteDialogVisible" title="确认删除" width="30%">
      <span>确定要删除此对话吗？此操作不可恢复。</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="confirmDeleteChat" :loading="isDeleting">删除</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, defineEmits, onMounted, watch } from 'vue'
import { Plus, ChatLineRound, Loading, MoreFilled, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { getUserChatList, createNewChat, updateChatTitle, deleteChat } from '@/services/chatService'
import { getUserInfo } from '@/services/auth'

const emit = defineEmits(['select-chat', 'chat-created'])

// 对话列表和状态
const chatList = ref([])
const activeChat = ref(null)
const loading = ref(false)
const userId = ref(null)

// 操作状态
const isCreating = ref(false)
const isRenaming = ref(false)
const isDeleting = ref(false)

// 对话框控制
const renameDialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const newChatTitle = ref('')
const currentEditChatId = ref(null)

// 获取用户ID
const userInfo = getUserInfo()
if (userInfo) {
  userId.value = userInfo.id
}

// 格式化时间
const formatTime = (date) => {
  if (!date) return ''
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

// 获取用户的对话列表
const fetchChatList = async () => {
  if (!userId.value) {
    ElMessage.warning('未登录或用户信息缺失')
    return
  }

  loading.value = true
  try {
    const response = await getUserChatList()
    chatList.value = response

    // 如果有对话且当前没有选中对话，默认选择第一个
    if (chatList.value.length > 0 && !activeChat.value) {
      activeChat.value = chatList.value[0].id
      emit('select-chat', activeChat.value)
    }
  } catch (error) {
    console.error('获取对话列表失败:', error)
    ElMessage.error('获取对话列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 创建新对话
const handleCreateChat = async () => {
  if (!userId.value) {
    ElMessage.warning('未登录或用户信息缺失')
    return
  }

  isCreating.value = true
  try {
    const response = await createNewChat(userId.value, '新对话')

    // 添加到列表顶部
    chatList.value.unshift(response)

    // 选择新创建的对话
    activeChat.value = response.id
    emit('select-chat', activeChat.value)
    emit('chat-created', response.id)

    ElMessage.success('已创建新对话')
  } catch (error) {
    console.error('创建新对话失败:', error)
    ElMessage.error('创建新对话失败，请稍后重试')
  } finally {
    isCreating.value = false
  }
}

// 选择对话
const selectChat = (chatId) => {
  activeChat.value = chatId
  emit('select-chat', chatId)
}

// 处理要删除的聊天
const handleDeleteChat = (chat) => {
  currentEditChatId.value = chat.id
  deleteDialogVisible.value = true
}

// 处理下拉菜单命令
const handleCommand = (command, chat) => {
  currentEditChatId.value = chat.id

  switch (command) {
    case 'rename':
      newChatTitle.value = chat.title
      renameDialogVisible.value = true
      break
    case 'delete':
      deleteDialogVisible.value = true
      break
  }
}

// 确认重命名对话
const confirmRenameChat = async () => {
  if (!newChatTitle.value.trim()) {
    ElMessage.warning('标题不能为空')
    return
  }

  isRenaming.value = true
  try {
    await updateChatTitle(currentEditChatId.value, newChatTitle.value.trim())

    // 更新本地列表
    const chatIndex = chatList.value.findIndex(chat => chat.id === currentEditChatId.value)
    if (chatIndex !== -1) {
      chatList.value[chatIndex].title = newChatTitle.value.trim()
    }

    ElMessage.success('对话已重命名')
    renameDialogVisible.value = false
  } catch (error) {
    console.error('重命名对话失败:', error)
    ElMessage.error('重命名失败，请稍后重试')
  } finally {
    isRenaming.value = false
  }
}

// 确认删除对话
const confirmDeleteChat = async () => {
  isDeleting.value = true
  try {
    await deleteChat(currentEditChatId.value)

    // 从本地列表移除
    chatList.value = chatList.value.filter(chat => chat.id !== currentEditChatId.value)

    // 如果删除的是当前选中的对话，需要选择一个新的对话
    if (activeChat.value === currentEditChatId.value) {
      if (chatList.value.length > 0) {
        activeChat.value = chatList.value[0].id
        emit('select-chat', activeChat.value)
      } else {
        activeChat.value = null
        emit('select-chat', null)
      }
    }

    ElMessage.success('对话已删除')
    deleteDialogVisible.value = false
  } catch (error) {
    console.error('删除对话失败:', error)
    ElMessage.error('删除失败，请稍后重试')
  } finally {
    isDeleting.value = false
  }
}

// 监听用户ID变化，重新加载对话列表
watch(() => userId.value, (newUserId) => {
  if (newUserId) {
    fetchChatList()
  } else {
    chatList.value = []
    activeChat.value = null
  }
})

// 组件挂载时获取对话列表
onMounted(() => {
  if (userId.value) {
    fetchChatList()
  }
})

// 暴露方法给父组件
defineExpose({
  fetchChatList,
});
</script>

<style scoped>
.history-sidebar {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.history-header {
  padding: 16px;
  border-bottom: 1px solid var(--el-border-color);

  h3 {
    margin: 0 0 12px 0;
    font-size: 16px;
  }
}

.history-sidebar-wrapper {
  width: 100%;
  height: 100%;
}

.history-list {
  flex: 1;
  min-height: 0;
}

.loading-wrapper,
.empty-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: var(--el-text-color-secondary);
  gap: 10px;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  margin: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: var(--el-color-primary-light-9);
  }

  &.active {
    background: var(--el-color-primary-light-8);
  }

  .item-content {
    display: flex;
    flex: 1;
    cursor: pointer;
    overflow: hidden;
  }

  .chat-icon {
    font-size: 18px;
    margin-right: 12px;
    color: var(--el-color-primary);
    flex-shrink: 0;
  }

  .action-buttons {
    display: flex;
    align-items: center;

    .delete-btn {
      margin-left: 8px;
      opacity: 0;
      /* 默认隐藏 */
      transition: opacity 0.2s ease;
    }
  }

  /* 当鼠标悬停在聊天项上时显示删除按钮 */
  &:hover .action-buttons .delete-btn {
    opacity: 1;
  }

  .content-wrapper {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    flex: 1;
    min-width: 0;

    .title-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;

      .title {
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        flex: 1;
      }
    }

    .preview {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-top: 4px;
    }

    .time {
      font-size: 12px;
      color: var(--el-text-color-placeholder);
      margin-top: 4px;
    }
  }
}

/* 暗黑模式适配 */
:root.dark .history-item,
html.dark .history-item,
.el-html--dark .history-item {
  &:hover {
    background: rgba(255, 255, 255, 0.05);
  }

  &.active {
    background: rgba(255, 255, 255, 0.08);
  }
}
</style>
