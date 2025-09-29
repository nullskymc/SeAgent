<template>
  <div class="main-page">
    <Header @toggle-collapse="toggleDrawer" @switch-tab="handleTabSwitch" :active-tab="activeTab" />
    <div class="main-container">
      <el-drawer
        v-model="isDrawerOpen"
        title="对话历史"
        direction="ltr"
        :with-header="false"
        size="240px"
        custom-class="history-drawer"
        v-show="activeTab === 'chat'"
      >
        <ChatHistory ref="chatHistoryRef" @select-chat="handleSelectChatInDrawer" />
      </el-drawer>

      <!-- 内容区域 -->
      <div class="content-wrapper">
        <!-- 聊天页面 -->
        <div v-show="activeTab === 'chat'" class="chat-container">
          <Chat :current-chat-id="currentChatId" class="chat-main" @title-updated="handleTitleUpdate" />
        </div>
        
        <!-- Python测试页面 -->
        <div v-show="activeTab === 'python-test'" class="python-test-container">
          <PythonTest />
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
import PythonTest from '@/components/PythonTest/PythonTest.vue';
import Footer from '@/components/Footer.vue';

const isDrawerOpen = ref(true); // 默认打开
const currentChatId = ref(null);
const chatHistoryRef = ref(null);
const activeTab = ref('chat'); // 默认显示聊天页面

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

// 处理选项卡切换
const handleTabSwitch = (tab) => {
  activeTab.value = tab;
  // 如果切换到非聊天页面，关闭侧边栏
  if (tab !== 'chat') {
    isDrawerOpen.value = false;
  }
};
</script>

<style>
.main-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--el-bg-color-page);
  position: relative;
}

.main-container {
  flex: 1;
  margin-top: 60px;
  display: flex;
  height: calc(100vh - 60px);
  position: relative;
  overflow: hidden;
  padding-bottom: 80px;
  box-sizing: border-box;
}

.content-wrapper {
  flex: 1;
  min-width: 0;
}

.chat-container {
  width: 100%;
  height: 100%;
  padding: 0;
}

.python-test-container {
  width: 100%;
  height: 100%;
  padding: 20px;
  overflow-y: auto;
  box-sizing: border-box;
}

/* 自定义抽屉样式 */
:deep(.history-drawer .el-drawer__body) {
  padding: 0;
}

/* 暗黑模式适配 */
:root.dark .main-page,
html.dark .main-page,
.el-html--dark .main-page {
  background-color: var(--el-bg-color);
  color: var(--el-text-color-primary);
}
</style>