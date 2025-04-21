import './assets/main.css'
import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import 'github-markdown-css/github-markdown.css'
import "highlight.js/styles/atom-one-dark.css";
import router from './router' // 导入router

const app = createApp(App)

app.use(ElementPlus)
app.use(router) // 使用router
app.mount('#app')
