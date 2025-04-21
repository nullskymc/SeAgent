<template>
  <div class="login-container">
    <div class="login-content">
      <el-card class="login-card">
        <div class="login-header">
          <h1 class="title">{{ isLogin ? '登录' : '注册' }}</h1>
        </div>

        <el-form :model="form" :rules="rules" ref="loginForm" @submit.prevent>
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" prefix-icon="User"></el-input>
          </el-form-item>

          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock"></el-input>
          </el-form-item>

          <el-form-item prop="email" v-if="!isLogin">
            <el-input v-model="form.email" placeholder="电子邮箱" prefix-icon="Message"></el-input>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" class="submit-btn" @click="submitForm" :loading="loading">
              {{ isLogin ? '登录' : '注册' }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-footer">
          <el-button text @click="toggleMode">
            {{ isLogin ? '没有账号？去注册' : '已有账号？去登录' }}
          </el-button>
        </div>
      </el-card>
    </div>
    
    <!-- 添加页脚组件 -->
    <Footer />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { login, register } from '@/services/auth'
import Footer from '@/components/Footer.vue'

const router = useRouter()
const loginForm = ref(null)
const loading = ref(false)
const isLogin = ref(true)

const form = reactive({
  username: '',
  password: '',
  email: ''
})

const rules = reactive({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入电子邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的电子邮箱地址', trigger: 'blur' }
  ]
})

const submitForm = async () => {
  if (!loginForm.value) return

  try {
    await loginForm.value.validate()
    loading.value = true

    if (isLogin.value) {
      // 登录
      const result = await login(form.username, form.password)
      ElMessage.success('登录成功')
      router.push('/main')
    } else {
      // 注册
      const result = await register(form.username, form.password, form.email)
      ElMessage.success('注册成功')
      router.push('/main')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error(isLogin.value ? '登录失败' : '注册失败')
  } finally {
    loading.value = false
  }
}

const toggleMode = () => {
  isLogin.value = !isLogin.value
}
</script>

<style scoped>
.login-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.login-content {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  padding: 20px;
}

.login-card {
  width: 400px;
  max-width: 90%;
  border-radius: 8px;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
}

.login-header {
  text-align: center;
  margin-bottom: 24px;
}

.title {
  font-size: 24px;
  color: var(--el-text-color-primary);
  margin: 0;
}

.submit-btn {
  width: 100%;
}

.login-footer {
  margin-top: 16px;
  text-align: center;
}

/* 暗黑模式适配 */
:root.dark .login-container,
html.dark .login-container,
.el-html--dark .login-container {
  background-color: #141414;
}

:root.dark .login-card,
html.dark .login-card,
.el-html--dark .login-card {
  background-color: #1d1d1d;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
}

:root.dark .title,
html.dark .title,
.el-html--dark .title {
  color: rgba(255, 255, 255, 0.85);
}
</style>