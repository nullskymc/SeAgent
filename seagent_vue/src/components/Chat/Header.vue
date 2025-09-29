<template>
  <el-header class="main-header" height="60px">
    <div class="header-container">
      <!-- 左侧区域 -->
      <div class="left-section">
        <el-button :icon="Menu" text circle @click="toggleCollapse" class="collapse-btn" />
        <img 
          src="@/images/logo.svg" 
          alt="Logo" 
          class="logo-btn"
        />
        <span class="app-title">智能代码助手</span>
        
        <!-- 统一导航菜单 -->
        <el-menu 
          mode="horizontal" 
          :default-active="activeMenuItem" 
          @select="handleMenuSelect"
          class="nav-menu"
        >
          <el-menu-item index="chat">
            <el-icon><ChatLineRound /></el-icon>
            <span>聊天</span>
          </el-menu-item>
          <el-menu-item index="python-test">
            <el-icon><Edit /></el-icon>
            <span>Python测试</span>
          </el-menu-item>
          <el-menu-item index="tools">
            <el-icon><Tools /></el-icon>
            <span>工具箱</span>
          </el-menu-item>
          <el-menu-item index="mcp-tools">
            <el-icon><Connection /></el-icon>
            <span>MCP工具</span>
          </el-menu-item>
          <el-menu-item index="knowledge">
            <el-icon><DataAnalysis /></el-icon>
            <span>知识库管理</span>
          </el-menu-item>
        </el-menu>
      </div>

      <!-- 右侧功能区 -->
      <div class="right-section">
        <!-- 主题切换 -->
        <el-tooltip effect="dark" :content="isDark ? '切换亮色模式' : '切换暗黑模式'" placement="bottom">
          <el-switch v-model="isDark" inline-prompt :active-icon="Moon" :inactive-icon="Sunny" @change="toggleTheme" />
        </el-tooltip>

        <!-- 用户信息 -->
        <div class="user-info">
          <span class="username">{{ username }}</span>
          <el-dropdown trigger="click">
            <el-button circle plain>
              <el-icon>
                <User />
              </el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>
  </el-header>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  User,
  Moon,
  Sunny,
  ChatLineRound,
  DataAnalysis,
  Tools,
  Connection,
  Menu,
  Edit
} from '@element-plus/icons-vue'
import { logout, getUserInfo } from '@/services/auth'

const props = defineProps({
  activeTab: {
    type: String,
    default: 'chat'
  }
})

const emit = defineEmits(['toggle-collapse', 'switch-tab'])
const router = useRouter()
const route = useRoute()

// 组件状态
const collapsed = ref(false)
const isDark = ref(false)
const username = ref('用户')

// 计算当前活动菜单项
const activeMenuItem = computed(() => {
  // 如果当前在主页面，根据activeTab确定选中项
  if (route.path === '/main') {
    return props.activeTab
  }
  // 对于其他路由，去掉前缀"/"
  return route.path.substring(1)
})

// 在组件挂载时获取用户信息
onMounted(() => {
  const userInfo = getUserInfo()
  if (userInfo && userInfo.username) {
    username.value = userInfo.username
  }
})

// 切换侧边栏
const toggleCollapse = () => {
  collapsed.value = !collapsed.value
  emit('toggle-collapse', collapsed.value)
}

// 统一处理菜单选择
const handleMenuSelect = (index) => {
  if (index === 'chat' || index === 'python-test') {
    // 内部页面切换，发射事件给Main组件处理
    if (route.path !== '/main') {
      router.push('/main')
    }
    emit('switch-tab', index)
  } else {
    // 外部页面路由跳转
    router.push(`/${index}`)
  }
}

// 主题切换处理
const toggleTheme = (isDark) => {
  if (isDark) {
    document.documentElement.classList.add('dark')
    document.documentElement.classList.remove('light')
  } else {
    document.documentElement.classList.add('light')
    document.documentElement.classList.remove('dark')
  }
}

// 退出登录
const handleLogout = () => {
  logout()
  router.push('/login')
}
</script>

<style scoped>
.main-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.header-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.left-section {
  display: flex;
  align-items: center;
  gap: 12px;

  .app-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin-right: 24px;
  }

  .app-logo {
    height: 32px;
    margin-right: 24px;
    object-fit: contain;
  }
}

.nav-menu {
  border-bottom: none;
  margin-left: 20px;
  flex: 1;
}

.right-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;

  .username {
    font-size: 14px;
    color: var(--el-text-color-regular);
    margin-right: 8px;
  }
}

/* logo 样式 */
.logo-btn {
  width: 100px;
  height: 100px;
  cursor: pointer;
  transition: transform 0.2s ease;
  margin-right: 8px;
  
  &:hover {
    transform: scale(1.1);
  }
}

/* 暗黑模式适配 */
:root.dark .main-header,
html.dark .main-header,
.el-html--dark .main-header {
  --el-bg-color: #141414;
  --el-border-color: #434343;
}

:root.dark .username,
html.dark .username,
.el-html--dark .username {
  color: rgba(255, 255, 255, 0.8);
}
</style>