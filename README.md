# 基于 RAG 的高校课程知识库智能问答系统

本项目是一个可完整演示的前后端分离课设系统。管理员可以创建课程、管理成员和资料；学生可以围绕课程文档进行带引用的流式问答，并生成摘要、知识点与测验。系统会保存会话、收藏、反馈和成绩，并在管理端汇总运营数据。

## 已实现功能

- JWT 注册、登录、刷新、退出与学生/管理员权限控制
- 课程创建、发布、加入、成员管理和课程隔离
- DOCX、PDF、TXT、Markdown 上传、解析、分块、向量化、重试和删除
- 基于课程范围的 Top-K 检索、SSE 流式回答、引用校验与无依据拒答
- 文档/课程摘要、核心知识点、关键词与复习建议
- 5/10 道单选题生成、服务端判分、来源与逐题解析
- 会话历史、回答收藏、反馈、学生学习统计与管理员看板
- PostgreSQL + pgvector、MinIO、本地 SQLite 开发模式和存储适配层
- Pytest、Vitest、Playwright 与 Docker Compose

## 一键启动

先确保 Docker Desktop 已运行，然后在项目根目录执行：

```powershell
docker compose up --build
```

服务地址：

- Web：<http://localhost:5173>
- API 文档：<http://localhost:8000/docs>
- MinIO 控制台：<http://localhost:9001>

首次启动会自动迁移数据库，并创建演示账号与课程。管理员登录后可直接上传 `课设提交模版/已经学过的知识点` 中的四份 DOCX 资料。

演示账号：

| 角色 | 邮箱 | 密码 |
|---|---|---|
| 管理员 | `admin@demo.com` | `Admin@123456` |
| 学生 | `student@demo.com` | `Student@123456` |

这些账号只用于 `APP_ENV=development` 的本地演示。生产环境必须在环境变量中更换密码与 `APP_SECRET`。

## 不使用 Docker 的开发方式

需要 Python 3.12 与 Node.js 20+。后端默认值支持 SQLite 和本地文件存储，启动时不要加载根目录中供 Compose 使用的 `.env`，可在独立终端显式覆盖：

```powershell
cd backend
$env:DATABASE_URL='sqlite:///./data/course_ai.db'
$env:STORAGE_MODE='local'
python -m pip install -e '.[test]'
python -m alembic upgrade head
python -m uvicorn main:app --reload --port 8000
```

另开终端：

```powershell
cd frontend
npm install
npm run dev
```

导入老师提供的四份演示资料：

```powershell
cd backend
python scripts/seed_demo.py
```

脚本通过公开 API 登录、上传和处理资料，可重复执行，已导入文件会自动跳过。

## 验证命令

```powershell
cd backend
python -m pytest -q

cd ../frontend
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

RAG 验收基准包含 20 个课程内问题和 5 个资料外问题。在演示数据导入且 API 运行后执行：

```powershell
cd backend
python scripts/run_rag_benchmark.py
```

Playwright 用例覆盖学生登录、进入课程、查看已处理资料、发起带引用问答、生成课程摘要和生成测验的主链路。

## 项目结构

```text
CourseDesign_01/
├─ frontend/                Vue 3、TypeScript、Element Plus
├─ backend/                 FastAPI、SQLAlchemy、Alembic、RAG
│  ├─ app/                  模型、服务、AI/存储适配器
│  ├─ migrations/           数据库版本迁移
│  ├─ scripts/seed_demo.py  演示资料导入
│  └─ tests/                接口与集成测试
├─ infra/                   pgvector 初始化脚本
├─ docs/                    架构、接口和演示说明
├─ 课设提交模版/            老师原始模板与资料，保持原样
├─ docker-compose.yml
└─ vercel.json              后续 Vercel Services 兼容配置
```

## AI 与存储模式

`AI_MODE=fake` 使用确定性的本地向量和回答，适合无密钥开发和稳定测试。真实验收时设置：

```dotenv
AI_MODE=dashscope
DASHSCOPE_API_KEY=your-key
DASHSCOPE_CHAT_MODEL=qwen-plus
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_DIMENSION=1024
```

AI 业务只调用 `embed()`、`generate()` 和 `generate_json()`，便于替换提供商。文件上传先获取上传说明；S3 模式由浏览器使用预签名 URL 直传，local 模式回退到 API 上传。

## 六人协作边界

| 模块 | 目录与接口责任 |
|---|---|
| 平台与认证 | `security.py`、`/auth/*`、登录注册页面 |
| 课程与成员 | Course/Member 模型、`/courses/*`、课程首页 |
| 文档与知识库 | `document_service.py`、`storage.py`、`/documents/*` |
| RAG 问答 | `ai.py`、Conversation/Message、SSE 与引用界面 |
| AI 学习工具 | Summary/Quiz 模型、摘要与测验页签 |
| 学习记录与分析 | Favorite/Feedback/Audit、学生与管理员看板 |

详细设计见 [架构说明](docs/ARCHITECTURE.md)、[接口说明](docs/API.md) 和 [演示脚本](docs/DEMO.md)。

## 后续 Vercel 部署准备

仓库保留前端与 FastAPI 独立入口。根配置也提供 `/server` 前缀的 Vercel Services 方案；使用它时设置前端变量 `VITE_API_BASE_URL=/server/api/v1`。正式部署前把数据库和文件配置切换到 Supabase PostgreSQL/pgvector 与 S3 兼容存储，并在 Vercel 中配置全部密钥。本阶段不执行线上部署。

未配置云数据库时，Vercel 会使用 `/tmp` 中的临时 SQLite 数据库启动演示账号。该模式便于预览界面，但冷启动可能重置数据；正式使用必须配置持久化 PostgreSQL 和对象存储。

## 开源许可

项目代码采用 [MIT License](LICENSE) 开源。
