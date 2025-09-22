<template>
  <footer class="app-footer">
    <div class="footer-content">
      <p class="copyright">
        © {{ currentYear }} PyAgent. 保留所有权利。
      </p>
      <p class="version">Version 1.0.0</p>
    </div>
  </footer>
</template>

<script setup>
import { ref, onMounted } from 'vue';

// 自动更新的当前年份
const currentYear = ref(new Date().getFullYear());
</script>

<style scoped>
.app-footer {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  width: auto;
  padding: 8px 20px;
  text-align: center;
  background-color: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1; /* 确保在内容之上 */
}

.footer-content {
  display: flex;
  align-items: center;
  gap: 16px; /* 在元素之间添加一些间距 */
}

.copyright {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.version {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin: 0;
}

/* 暗黑模式适配 */
:root.dark .app-footer,
html.dark .app-footer,
.el-html--dark .app-footer {
  background-color: #2c2c2f;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}
</style>