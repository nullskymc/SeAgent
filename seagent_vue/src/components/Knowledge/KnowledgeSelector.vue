<template>
  <div class="knowledge-selector">
    <el-select
      v-model="selectedCollection"
      placeholder="选择知识库"
      clearable
      @change="handleCollectionChange"
    >
      <el-option
        v-for="item in collections"
        :key="item"
        :label="item"
        :value="item"
      />
      <template #prefix>
        <el-icon><DataAnalysis /></el-icon>
      </template>
      <template #empty>
        <div class="empty-list">
          <p>暂无知识库</p>
          <el-link type="primary" @click="goToKnowledgePage">前往创建</el-link>
        </div>
      </template>
    </el-select>
    
    <el-tooltip
      effect="dark"
      content="使用此知识库回答问题"
      placement="top"
      v-if="selectedCollection"
    >
      <span class="selected-label">
        已选择知识库: <strong>{{ selectedCollection }}</strong>
      </span>
    </el-tooltip>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { DataAnalysis } from '@element-plus/icons-vue';
import { getKnowledgeCollections } from '@/services/knowledgeService';

// 向父组件提供事件
const emit = defineEmits(['collection-change']);

// 路由器
const router = useRouter();

// 组件状态
const collections = ref([]);
const selectedCollection = ref('');
const loading = ref(false);

// 获取知识库列表
const fetchCollections = async () => {
  try {
    loading.value = true;
    const result = await getKnowledgeCollections();
    collections.value = result || [];
  } catch (error) {
    console.error('获取知识库列表失败', error);
    ElMessage.error('获取知识库列表失败');
  } finally {
    loading.value = false;
  }
};

// 处理知识库切换
const handleCollectionChange = (value) => {
  emit('collection-change', value);
};

// 跳转到知识库管理页面
const goToKnowledgePage = () => {
  router.push('/knowledge');
};

// 组件挂载时获取知识库列表
onMounted(() => {
  fetchCollections();
});
</script>

<style scoped>
.knowledge-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.el-select {
  min-width: 180px;
}

.empty-list {
  padding: 8px;
  text-align: center;
}

.selected-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

/* 暗黑模式适配 */
:root.dark .knowledge-selector,
html.dark .knowledge-selector,
.el-html--dark .knowledge-selector {
  background-color: var(--el-bg-color-overlay);
  border-color: var(--el-border-color-darker);
}

:root.dark .knowledge-title,
html.dark .knowledge-title,
.el-html--dark .knowledge-title {
  color: rgba(255, 255, 255, 0.85);
}
</style>