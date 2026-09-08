# 基于RAG的医疗领域智能问答系统

## 项目简介
基于RAG（检索增强生成）技术构建的医疗领域智能问答系统，通过医学知识库为用户提供准确、可溯源的专业问答服务。

## 技术栈
- 后端：FastAPI + LlamaIndex + ChromaDB
- 前端：Vue.js 3 + Element Plus + axios
- 部署：Docker + Docker Compose
- AI：DashScope通义千问

## 快速开始

### 方式一：Docker一键部署（推荐）
```bash
# 1. 复制环境变量文件并配置API Key
cp .env.example .env
# 编辑.env文件，填入你的DASHSCOPE_API_KEY

# 2. 启动所有服务
docker-compose up -d --build

# 3. 访问系统
# 前端：http://localhost
# API文档：http://localhost:8000/docs
```

### 方式二：本地开发模式
```bash
# 后端
cd backend
conda create -n rag-qa python=3.10 -y
conda activate rag-qa
pip install -r requirements.txt
python main.py

# 前端
cd frontend
npm install
npm run dev
```

## 项目结构
```
├── backend/           # 后端代码
│   ├── main.py        # FastAPI入口
│   ├── config.py      # 配置管理
│   ├── auth/          # 认证模块（JWT+bcrypt）
│   ├── documents/     # 文档管理模块
│   ├── rag/           # RAG引擎模块
│   └── chat/          # 对话管理模块
├── frontend/          # Vue前端代码
│   └── src/
│       ├── views/     # 页面组件
│       ├── api/       # API封装
│       └── utils/     # 工具函数
├── docker/            # Docker配置
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   └── nginx.conf
├── docker-compose.yml # Docker Compose编排
└── .env.example       # 环境变量模板
```

## 团队成员
- 组长：张三（软件2301班）
- 组员：李四、王五、赵六、钱七
