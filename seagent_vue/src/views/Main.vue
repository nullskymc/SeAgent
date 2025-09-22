<template>
  <div id="app">
    <Header @toggle-collapse="toggleDrawer" />
    <div class="main-container">
      <el-drawer
        v-model="isDrawerOpen"
        title="对话历史"
        direction="ltr"
        :with-header="false"
        size="240px"
        custom-class="history-drawer"
      >
        <ChatHistory ref="chatHistoryRef" @select-chat="handleSelectChatInDrawer" />
      </el-drawer>

      <div class="chat-wrapper">
        <div class="chat-container">
          <Chat :current-chat-id="currentChatId" class="chat-main" @title-updated="handleTitleUpdate" />
        </div>
      </div>
    </div>
    <Footer />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import Header from '@/components/Chat/Header.vue';
import ChatHistory from '@/components/Chat/ChatHistory.vue';
import Chat from '@/components/Chat/Chat.vue';
import Footer from '@/components/Footer.vue';

const isDrawerOpen = ref(true); // 默认打开
const currentChatId = ref(null);
const chatHistoryRef = ref(null);

const toggleDrawer = () => {
  isDrawerOpen.value = !isDrawerOpen.value;
};

const handleSelectChat = (chatId) => {
  currentChatId.value = chatId;
};

// 在抽屉中选择对话后，如果是移动端则关闭抽屉
const handleSelectChatInDrawer = (chatId) => {
  currentChatId.value = chatId;
  if (window.innerWidth < 768) {
    isDrawerOpen.value = false;
  }
};

const handleTitleUpdate = () => {
  if (chatHistoryRef.value) {
    chatHistoryRef.value.fetchChatList();
  }
};
</script>

<style>
#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--el-bg-color-page);
  position: relative; /* 添加此行以作为页脚定位的上下文 */
}

.main-container {
  flex: 1;
  margin-top: 60px;
  display: flex;
  height: calc(100vh - 60px);
  position: relative;
  overflow: hidden;
  padding-bottom: 80px; /* 为悬浮页脚留出空间 */
  box-sizing: border-box; /* 确保padding正确计算 */
}

.chat-wrapper {
  flex: 1;
  min-width: 0;
}

.chat-container {
  width: 100%;
  height: 100%;
  padding: 0;
}

/* 自定义抽屉样式 */
:deep(.history-drawer .el-drawer__body) {
  padding: 0;
}

/* 暗黑模式适配 */
:root.dark #app,
html.dark #app,
.el-html--dark #app {
  background-color: var(--el-bg-color);
  color: var(--el-text-color-primary);
}
</style>