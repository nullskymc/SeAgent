<template>
  <div id="app-root">
    <router-view></router-view>
  </div>
</template>

<script>
import Index from '@/views/Index.vue';

export default {
  components: {
    Index
  }
}
</script>


<style>
/* 确保根渲染区域填满视口且不强制滚动，由各页面自行控制 */
#app-root {
  min-height: 100vh;
}
</style>


