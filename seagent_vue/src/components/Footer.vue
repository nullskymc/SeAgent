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
  width: 100%;
  padding: 12px 0;
  text-align: center;
  background-color: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-light);
  margin-top: auto;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.copyright {
  font-size: 14px;
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
  border-top-color: var(--el-border-color-darker);
}
</style>