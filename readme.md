# SeAgent: 智能对话助手

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0+-green.svg)
![Vue](https://img.shields.io/badge/Vue-3.x-brightgreen.svg)
![LangChain](https://img.shields.io/badge/LangChain-Latest-orange.svg)

SeAgent是一个基于Python和Vue.js开发的智能对话系统，支持知识库增强的AI对话，采用大语言模型提供问答服务。系统支持用户管理、多轮对话、知识库管理等功能。

## 功能特性

### 核心功能
- **智能对话**: 基于大语言模型的自然对话能力
- **知识库增强**: 支持上传文档创建知识库，使AI回答基于特定领域知识
- **多轮对话**: 支持上下文关联的多轮对话
- **用户系统**: 完整的用户注册、登录和认证功能
- **对话管理**: 创建、查看、删除对话历史
- **主题切换**: 支持亮色/暗色主题切换

### 技术特点
- **前后端分离**: FastAPI后端 + Vue.js前端
- **向量存储**: 使用Chroma向量数据库进行语义检索
- **模型适配**: 支持多种大型语言模型接口
- **工具代理**: 基于LangChain实现的智能代理功能

## 技术栈

### 后端
- **FastAPI**: Web框架
- **SQLite**: 数据库
- **LangChain**: 大语言模型工具链
- **Chroma**: 向量数据库
- **JWT**: 身份认证

### 前端
- **Vue 3**: 前端框架
- **Element Plus**: UI组件库
- **Vue Router**: 路由管理
- **Axios**: HTTP客户端

## 安装与部署

### 环境要求
- Python 3.9+
- Node.js 14+
- npm/yarn

### 后端部署

1. **克隆仓库**
   ```bash
   git clone https://github.com/yourusername/SeAgent.git
   cd SeAgent
   ```

2. **创建并激活虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或 
   .\venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   
   创建`.env`文件，配置以下环境变量:
   ```
   OPENAI_API_KEY=your_api_key
   OPENAI_API_BASE=https://api.openai.com/v1
   OPENAI_MODEL_NAME=gpt-4 # 或其他模型
   OPENAI_EMBEDDING_MODEL=text-embedding-3-small # 或其他嵌入模型
   ```

5. **运行后端服务**
   ```bash
   uvicorn fast_app:app --host 0.0.0.0 --port 8000 --reload
   ```

### 前端部署

1. **进入前端目录**
   ```bash
   cd SeAgent_vue
   ```

2. **安装依赖**
   ```bash
   npm install
   # 或
   yarn install
   ```

3. **开发模式运行**
   ```bash
   npm run dev
   # 或
   yarn dev
   ```

4. **构建生产版**
   ```bash
   npm run build
   # 或
   yarn build
   ```

### 使用Docker部署

1. **构建Docker镜像**
   ```bash
   docker build -t seagent:latest .
   ```

2. **运行Docker容器**
   ```bash
   docker run -d -p 8000:8000 --name seagent --env-file .env seagent:latest
   ```

## 使用指南

### 用户注册与登录
1. 访问首页，点击"登录系统"
2. 首次使用请点击"没有账号？去注册"
3. 填写用户名、密码和电子邮箱完成注册
4. 使用注册的账号登录系统

### 开始对话
1. 登录后自动进入主界面
2. 点击左侧"新对话"按钮创建聊天
3. 在底部输入框中输入问题并发送
4. 系统会显示AI助手的回复

### 知识库管理
1. 点击顶部导航栏的"知识库管理"
2. 在上传区域填写知识库名称
3. 上传TXT、PDF或CSV格式文件
4. 点击"上传到知识库"按钮
5. 上传成功后在知识库列表中可以看到已创建的知识库

### 使用知识库回答问题
1. 在聊天界面，使用顶部的知识库选择器选择一个知识库
2. 发送的问题将基于选中的知识库进行回答
3. 系统会在回答中引用相关知识

## 项目结构

```
SeAgent/
├── adapter/              # 模型适配器
├── database/             # 数据库模型和操作
│   ├── models/           # 数据模型定义
│   └── ...
├── routes/               # API路由
├── utils/                # 工具函数
│   ├── tools/            # 代理工具
│   └── ...
├── SeAgent_vue/          # 前端Vue项目
│   ├── src/              # 源代码
│   │   ├── components/   # 组件
│   │   ├── views/        # 页面
│   │   ├── services/     # API服务
│   │   └── ...
│   └── ...
├── vector_db/            # 向量数据库存储
├── fast_app.py           # 主应用入口
└── requirements.txt      # 依赖列表
```

## 贡献指南

欢迎为SeAgent项目做出贡献！以下是参与开发的基本步骤：

1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启Pull Request

## 许可证

该项目采用MIT许可证 - 详细信息请参见 [LICENSE](LICENSE) 文件

