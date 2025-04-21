<template>
  <div id="app">
    <Header @toggle-collapse="handleCollapse" />
    <div class="main-container">
      <ChatHistory :class="{ collapsed: isCollapsed }" @select-chat="handleSelectChat" />
      <div class="chat-wrapper" :class="{ collapsed: isCollapsed }">
        <div class="chat-container">
          <Chat :current-chat-id="currentChatId" class="chat-main" />
        </div>
      </div>
    </div>
    <!-- 添加页脚组件 -->
    <Footer />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Header from '@/components/Chat/Header.vue'
import ChatHistory from '@/components/Chat/ChatHistory.vue'
import Chat from '@/components/Chat/Chat.vue'
import Footer from '@/components/Footer.vue'

const isCollapsed = ref(false)
const currentChatId = ref(null)

const handleCollapse = (collapsed) => {
  isCollapsed.value = collapsed
}

const handleSelectChat = (chatId) => {
  currentChatId.value = chatId
}
</script>

<style>
#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-container {
  flex: 1;
  margin-top: 60px;
  display: flex;
  height: calc(100vh - 60px);
  position: relative;
  overflow: hidden;
}

.chat-history-wrapper {
  width: 240px;
  flex-shrink: 0;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat-main {
  overflow: visible;
  flex: 1;
  min-width: 0;
  margin-right: 16px;
  width: calc(100% - 16px);
  transform: translateX(0);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat-wrapper {
  flex: 1;
  position: relative;
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &.collapsed {
    margin-left: 0;
  }
}

.chat-container {
  max-width: 1400px;
  margin: auto 0;
  height: calc(100% - 20px);
  padding: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat-wrapper.collapsed .chat-container {
  margin-left: 0;
  max-width: 1400px;
}

/* 侧边栏收起时的状态 - 更新选择器，移除不正确CSS */
.main-container .chat-main {
  width: calc(100% - 24px);
  margin-left: 0;
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@media (max-width: 768px) {
  .chat-history-wrapper.collapsed {
    transform: translateX(-100%);
  }

  .chat-main {
    margin-left: 0;
    width: 100%;
  }
}

/* 暗黑模式适配 */
:root.dark #app,
html.dark #app,
.el-html--dark #app {
  background-color: var(--el-bg-color);
  color: var(--el-text-color-primary);
}

:root.dark .main-container,
html.dark .main-container,
.el-html--dark .main-container {
  background-color: var(--el-bg-color);
}

:root.dark .chat-container,
html.dark .chat-container,
.el-html--dark .chat-container {
  background-color: var(--el-bg-color);
}
</style>