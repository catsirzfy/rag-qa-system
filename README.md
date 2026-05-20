# SmartKB 企业知识库问答系统

基于检索增强生成（RAG）的企业级智能文档问答平台。

## 产品概述

SmartKB 是面向企业的智能知识库系统。管理员上传企业文档后，员工可通过自然语言提问，系统自动从文档中检索相关信息并生成准确回答。支持权限分级、操作审计、流式输出。

## 核心功能

| 模块 | 功能 |
|------|------|
| 📄 文档管理 | 上传 Markdown/TXT/PDF，自动解析、分块、向量索引 |
| 🔍 语义检索 | 基于向量相似度的智能文档搜索 |
| 💬 AI 问答 | 结合检索结果生成精准回答，支持流式逐字输出 |
| 🔐 权限控制 | 管理员 vs 普通用户，上传/删除仅限管理员 |
| 📋 审计日志 | 记录所有问答历史，支持查询与删除 |
| 👥 用户管理 | 增删改查用户，启用/禁用账号 |

## 技术架构

```
前端(HTML/CSS/JS) → FastAPI → LangChain RAG → DeepSeek LLM
                         ├── ChromaDB 向量库
                         ├── SQLite 业务数据库
                         └── BAAI/bge-small-zh 本地 Embedding
```

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| 后端框架 | FastAPI（异步） |
| AI 框架 | LangChain（LCEL 管道） |
| 向量数据库 | ChromaDB |
| 大语言模型 | DeepSeek Chat（兼容 OpenAI） |
| Embedding | BAAI/bge-small-zh（本地部署，90MB） |
| 数据库 | SQLite（SQLAlchemy 2.0 异步 ORM） |
| 认证 | JWT（python-jose） |
| 前端 | 原生 HTML/CSS/JS（零依赖，纯浏览器） |
| 部署 | Docker + Docker Compose |

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env   # 编辑填入 DEEPSEEK_API_KEY

# 启动服务
python -m uvicorn main:app --port 8000

# 浏览器打开 http://localhost:8000
```

## 测试账号

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 上传文档、管理用户、查看审计 |
| 员工 | staff001 | staff123 | 仅问答 |

## Docker 部署

```bash
docker compose up -d --build
# 首次构建需下载模型（~90MB），之后秒启动
# 数据持久化在 chroma_db/ 和 app.db 中，容器删除不丢数据
```

## 项目结构

```
├── app/
│   ├── api/              # FastAPI 路由层（client + backoffice）
│   ├── core/             # 配置 + JWT 安全模块
│   ├── db/               # 数据库引擎 + 会话管理
│   ├── models/           # SQLAlchemy ORM 模型
│   ├── schemas/          # Pydantic 数据校验
│   ├── services/         # 业务逻辑层
│   ├── exceptions/       # 统一异常体系
│   └── route/            # 路由注册中心
├── static/               # 前端页面
├── main.py               # 应用入口
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## License

MIT
