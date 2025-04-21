import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Main from '../views/Main.vue'
import Knowledge from '../views/Knowledge.vue'
import Index from '../views/Index.vue'
import Tools from '../views/Tools.vue'  // 导入工具页面组件

const routes = [
  {
    // 恢复原始配置，保持根路径指向Index组件
    path: '/',
    name: 'Index',
    component: Index
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/main',
    name: 'Main',
    component: Main
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: Knowledge
  },
  {
    path: '/tools',   // 添加工具页面路由
    name: 'Tools',
    component: Tools
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 添加导航守卫，检查登录状态并自动重定向到登录页面
// router.beforeEach((to, from, next) => {
//   // 获取本地存储的token
//   const token = localStorage.getItem('token');

//   // 如果是首页且没有登录，重定向到登录页面
//   if (to.path === '/' && !token) {
//     next('/login');
//   } else {
//     next();
//   }
// });

export default router
