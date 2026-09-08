# API 接口说明

服务根路径为 `/api/v1`。成功响应包含 `data`、`message`、`request_id`；失败响应额外包含稳定的 `code`。除注册、登录和健康检查外，请求使用 `Authorization: Bearer <access_token>`。

| 模块 | 方法与路径 | 用途 |
|---|---|---|
| 认证 | `POST /auth/register` | 学生注册 |
| 认证 | `POST /auth/login` | 登录并获取双 Token |
| 认证 | `POST /auth/refresh`、`POST /auth/logout` | 轮换或撤销 Refresh Token |
| 认证 | `GET /auth/me` | 当前用户 |
| 课程 | `GET/POST /courses` | 列表或创建课程 |
| 课程 | `GET/PATCH/DELETE /courses/{id}` | 课程详情与管理 |
| 成员 | `POST /courses/join` | 通过课程码加入 |
| 成员 | `GET/POST/DELETE /courses/{id}/members` | 成员管理 |
| 文档 | `POST /documents/upload-url` | 获取预签名或本地上传说明 |
| 文档 | `POST /courses/{id}/documents` | 登记对象存储结果 |
| 文档 | `POST /documents/upload-local` | 本地开发直传 |
| 文档 | `POST /documents/{id}/process` | 幂等解析和向量化 |
| 文档 | `GET/DELETE /documents/{id}` | 查询或删除文档 |
| 对话 | `POST/GET /conversations` | 创建或查询会话 |
| 问答 | `POST /conversations/{id}/messages` | SSE 流式问答 |
| 摘要 | `POST /documents/{id}/summary` | 文档摘要 |
| 摘要 | `POST /courses/{id}/summary` | 课程摘要 |
| 测验 | `POST /courses/{id}/quizzes` | 生成 5/10 道题 |
| 测验 | `GET /quizzes/{id}` | 获取不含答案的题目 |
| 测验 | `POST /quizzes/{id}/submit` | 服务端判分与解析 |
| 记录 | `POST /messages/{id}/favorite` | 收藏/取消收藏 |
| 记录 | `POST /messages/{id}/feedback` | 提交回答评价 |
| 看板 | `GET /dashboard/student` | 学习统计 |
| 看板 | `GET /dashboard/admin` | 平台统计与审计 |

SSE 事件顺序为：

```text
event: retrieval  data: {"count": 8}
event: token      data: {"text": "..."}
event: citations data: [{"source_id":"S1", ...}]
event: done       data: {"message": {...}}
```

运行后可在 <http://localhost:8000/docs> 查看带请求模型的交互式 OpenAPI 页面。
