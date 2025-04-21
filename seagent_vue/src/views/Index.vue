<template>
  <div class="index-container">
    <div class="index-content">
      <div class="welcome-box">
        <img src="@/images/logo.svg" alt="Logo" class="logo">
        <h1>欢迎使用智能代码助手</h1>
        <p>您的智能Python 学习伙伴，随时为您提供帮助</p>

        <div class="action-buttons">
          <el-button type="primary" size="large" @click="goToLoginPage">账户登录</el-button>
          <el-button type="success" size="large" @click="goToMainPage">直接开始</el-button>
        </div>
      </div>
    </div>
    <!-- 添加页脚组件 -->
    <Footer />
  </div>
</template>

<script setup>
import Footer from '@/components/Footer.vue';
</script>

<script>
export default {
  mounted() {
    // 检查是否已登录，如果已登录则自动跳转到main页面
    const token = localStorage.getItem('token');
    if (token) {
      this.$router.push('/main');
    }
  },
  methods: {
    goToLoginPage() {
      this.$router.push('/login');
    },
    goToMainPage() {
      this.$router.push('/main');
    }
  }
}
</script>

<style scoped>
.index-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.index-content {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  padding: 20px;
}

.welcome-box {
  text-align: center;
  padding: 40px;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  max-width: 500px;
  width: 90%;
}

.logo {
  width: 250px;
  margin-bottom: 20px;
}

h1 {
  font-size: 28px;
  color: #303133;
  margin-bottom: 16px;
}

p {
  color: #606266;
  margin-bottom: 32px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
}

/* 暗黑模式适配 */
:root.dark .index-container,
html.dark .index-container,
.el-html--dark .index-container {
  background-color: #141414;
}

:root.dark .welcome-box,
html.dark .welcome-box,
.el-html--dark .welcome-box {
  background-color: #1d1d1d;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
}

:root.dark h1,
html.dark h1,
.el-html--dark h1 {
  color: rgba(255, 255, 255, 0.85);
}

:root.dark p,
html.dark p,
.el-html--dark p {
  color: rgba(255, 255, 255, 0.65);
}
</style>