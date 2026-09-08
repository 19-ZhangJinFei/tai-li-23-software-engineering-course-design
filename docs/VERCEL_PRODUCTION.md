# Vercel 正式演示部署清单

## 所需云端资源

1. Supabase PostgreSQL：在项目的 **Connect** 面板复制 Transaction pooler 连接串（端口 `6543`）。
2. Supabase Storage：在 Storage 设置中启用 S3 protocol，生成一组仅供服务端使用的 Access Key ID 与 Secret Access Key，并记录 endpoint 与 region。
3. 阿里云百炼：创建可调用 `qwen-plus` 与 `text-embedding-v4` 的 DashScope API Key。
4. Vercel：在项目设置中录入下列环境变量，或提供可用于 CLI 的部署令牌。

## Vercel 环境变量

| 名称 | 来源或值 |
|---|---|
| `APP_ENV` | `production` |
| `APP_SECRET` | 随机生成的至少 32 字符密钥 |
| `FRONTEND_ORIGIN` | `https://tai-li-course-ai.vercel.app` |
| `DATABASE_URL` | Supabase Transaction pooler 连接串 |
| `STORAGE_MODE` | `s3` |
| `STORAGE_BUCKET` | `course-documents` |
| `STORAGE_ENDPOINT` | Supabase S3 endpoint |
| `STORAGE_PUBLIC_ENDPOINT` | 与 S3 endpoint 相同 |
| `STORAGE_ACCESS_KEY` | Supabase S3 Access Key ID |
| `STORAGE_SECRET_KEY` | Supabase S3 Secret Access Key |
| `STORAGE_REGION` | Supabase 项目 region |
| `AI_MODE` | `dashscope` |
| `DASHSCOPE_API_KEY` | 阿里云百炼 API Key |
| `DASHSCOPE_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `DASHSCOPE_CHAT_MODEL` | `qwen-plus` |
| `DASHSCOPE_EMBEDDING_MODEL` | `text-embedding-v4` |
| `EMBEDDING_DIMENSION` | `1024` |
| `AUTO_APPROVE_REGISTRATION` | `true`（答辩演示） |

应用会把普通 `postgresql://` 连接串转换为 psycopg 3 格式，并针对 Supavisor Transaction pooler 禁用客户端连接池和预编译语句。S3 bucket 不存在时会在冷启动阶段自动创建。

## 上线验收顺序

1. `/server/health` 返回 `database=postgresql`、`storage=s3`、`ai_mode=dashscope`。
2. 管理员登录，创建课程、添加成员并上传 Markdown、TXT、DOCX、PDF 各一份。
3. 四份文档均从“待处理”进入“可检索”，刷新和冷启动后状态保持不变。
4. 学生注册、加入课程、重新登录，刷新和冷启动后仍能访问课程。
5. 课程内问题返回流式正文和可核对引用；课程外问题明确拒答。
6. 生成课程摘要和 5 道测验题，提交后显示分数、解析与来源。
7. 收藏回答、提交正负反馈，在学生看板和管理员看板核对统计。
8. 重新部署同一提交后复查用户、课程、文档、对话、收藏和成绩仍存在。
9. 检查浏览器控制台、Vercel 构建日志和运行时错误，确认没有未处理异常。

该顺序覆盖老师要求的“项目演示 + 报告内容检查”，并可在 20 分钟内按管理员、学生、AI 学习工具、管理统计四段完成现场展示。
