<template>
  <div class="tools-container">
    <Header />

    <div class="content-wrapper">
      <div class="content-container">
      <h1>工具箱</h1>

      <div class="tools-grid">
        <!-- 代码分析工具 -->
        <el-card class="tool-card">
          <template #header>
            <div class="card-header">
              <h3>代码分析工具</h3>
              <el-tag type="primary" effect="plain">代码助手</el-tag>
            </div>
          </template>

          <div class="tool-content">
            <p class="description">分析代码结构，包括函数、类、导入和变量等</p>
            <div class="feature-list">
              <div class="feature-item">
                <el-icon><DocumentCopy /></el-icon>
                <span>识别代码结构与组件</span>
              </div>
              <div class="feature-item">
                <el-icon><Connection /></el-icon>
                <span>分析函数和类关系</span>
              </div>
              <div class="feature-item">
                <el-icon><Search /></el-icon>
                <span>检测潜在问题</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 代码生成工具 -->
        <el-card class="tool-card">
          <template #header>
            <div class="card-header">
              <h3>代码生成工具</h3>
              <el-tag type="success" effect="plain">代码助手</el-tag>
            </div>
          </template>

          <div class="tool-content">
            <p class="description">根据描述生成代码片段，支持多种编程语言</p>
            <div class="feature-list">
              <div class="feature-item">
                <el-icon><Promotion /></el-icon>
                <span>自然语言转代码</span>
              </div>
              <div class="feature-item">
                <el-icon><Finished /></el-icon>
                <span>支持多种编程语言</span>
              </div>
              <div class="feature-item">
                <el-icon><Edit /></el-icon>
                <span>定制化代码生成</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 代码修复工具 -->
        <el-card class="tool-card">
          <template #header>
            <div class="card-header">
              <h3>代码修复工具</h3>
              <el-tag type="warning" effect="plain">代码助手</el-tag>
            </div>
          </template>

          <div class="tool-content">
            <p class="description">自动检测并修复代码中的错误和问题</p>
            <div class="feature-list">
              <div class="feature-item">
                <el-icon><CircleCheck /></el-icon>
                <span>语法错误修正</span>
              </div>
              <div class="feature-item">
                <el-icon><Refresh /></el-icon>
                <span>代码优化建议</span>
              </div>
              <div class="feature-item">
                <el-icon><Opportunity /></el-icon>
                <span>逻辑问题检测</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 代码文档工具 -->
        <el-card class="tool-card">
          <template #header>
            <div class="card-header">
              <h3>代码文档工具</h3>
              <el-tag type="info" effect="plain">代码助手</el-tag>
            </div>
          </template>

          <div class="tool-content">
            <p class="description">为代码生成文档字符串和注释</p>
            <div class="feature-list">
              <div class="feature-item">
                <el-icon><Document /></el-icon>
                <span>自动生成文档</span>
              </div>
              <div class="feature-item">
                <el-icon><Notebook /></el-icon>
                <span>标准格式注释</span>
              </div>
              <div class="feature-item">
                <el-icon><Reading /></el-icon>
                <span>提高代码可读性</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 依赖分析工具 -->
        <el-card class="tool-card">
          <template #header>
            <div class="card-header">
              <h3>依赖分析工具</h3>
              <el-tag type="danger" effect="plain">代码助手</el-tag>
            </div>
          </template>

          <div class="tool-content">
            <p class="description">分析代码依赖，识别导入的库并提供安装建议</p>
            <div class="feature-list">
              <div class="feature-item">
                <el-icon><Box /></el-icon>
                <span>识别第三方库</span>
              </div>
              <div class="feature-item">
                <el-icon><Download /></el-icon>
                <span>生成安装命令</span>
              </div>
              <div class="feature-item">
                <el-icon><Link /></el-icon>
                <span>检测环境依赖</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 代码质量检查 -->
        <el-card class="tool-card">
          <template #header>
            <div class="card-header">
              <h3>代码质量检查</h3>
              <el-tag type="primary" effect="plain">代码审查</el-tag>
            </div>
          </template>

          <div class="tool-content">
            <p class="description">检查代码质量，提供改进建议</p>
            <div class="feature-list">
              <div class="feature-item">
                <el-icon><Odometer /></el-icon>
                <span>代码质量评分</span>
              </div>
              <div class="feature-item">
                <el-icon><SetUp /></el-icon>
                <span>命名规范检查</span>
              </div>
              <div class="feature-item">
                <el-icon><ScaleToOriginal /></el-icon>
                <span>代码复杂度分析</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 安全审查工具 -->
        <el-card class="tool-card">
          <template #header>
            <div class="card-header">
              <h3>安全审查工具</h3>
              <el-tag type="success" effect="plain">代码审查</el-tag>
            </div>
          </template>

          <div class="tool-content">
            <p class="description">对代码进行安全性审查，检查常见的安全漏洞</p>
            <div class="feature-list">
              <div class="feature-item">
                <el-icon><Lock /></el-icon>
                <span>漏洞检测</span>
              </div>
              <div class="feature-item">
                <el-icon><Warning /></el-icon>
                <span>风险评估</span>
              </div>
              <div class="feature-item">
                <el-icon><Umbrella /></el-icon>
                <span>安全修复建议</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 最佳实践工具 -->
        <el-card class="tool-card">
          <template #header>
            <div class="card-header">
              <h3>最佳实践工具</h3>
              <el-tag type="warning" effect="plain">代码审查</el-tag>
            </div>
          </template>

          <div class="tool-content">
            <p class="description">根据编程语言的最佳实践，提供代码改进建议</p>
            <div class="feature-list">
              <div class="feature-item">
                <el-icon><Stamp /></el-icon>
                <span>语言特定优化</span>
              </div>
              <div class="feature-item">
                <el-icon><MagicStick /></el-icon>
                <span>代码简化建议</span>
              </div>
              <div class="feature-item">
                <el-icon><TrendCharts /></el-icon>
                <span>性能改进方案</span>
              </div>
            </div>
          </div>
        </el-card>

              </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import Header from '@/components/Chat/Header.vue';
import {
  DocumentCopy, Connection, Search, Promotion, Finished, Edit,
  CircleCheck, Refresh, Opportunity, Document, Notebook, Reading,
  Box, Download, Link, Odometer, SetUp, ScaleToOriginal,
  Lock, Warning, Umbrella, Stamp, MagicStick, TrendCharts
} from '@element-plus/icons-vue';

</script>

<style scoped>
.tools-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  /* 根容器不滚动，避免嵌套滚动冲突 */
  overflow: hidden;
  position: relative;
}

.content-wrapper {
  position: absolute;
  top: 60px; /* 为固定头部留出空间 */
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: auto;
}

.content-container {
  padding: 20px 24px 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  /* 由外层 content-wrapper 负责滚动 */
}

h1 {
  margin-bottom: 32px;
  font-size: 28px;
  color: var(--el-text-color-primary);
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
}

.tool-card {
  height: 100%;
  transition: all 0.3s ease;
}

.tool-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
}

.tool-content {
  padding: 10px 0;
}

.description {
  margin-bottom: 20px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.feature-item .el-icon {
  font-size: 18px;
  color: var(--el-color-primary);
}

/* 暗黑模式适配 */
:root.dark .tools-container,
html.dark .tools-container,
.el-html--dark .tools-container {
  background-color: var(--el-bg-color);
}

:root.dark .tool-card:hover,
html.dark .tool-card:hover,
.el-html--dark .tool-card:hover {
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
}
</style>