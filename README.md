# RAG 知识库问答系统

基于检索增强生成的企业级知识库问答系统，支持文档上传、语义检索、流式输出。

## 功能

- 📄 文档上传与自动索引（Markdown、TXT、PDF）
- 🔍 语义检索（LangChain + ChromaDB 向量数据库）
- 💬 AI 问答（DeepSeek / OpenAI 兼容）
- 📡 SSE 流式输出
- 🎨 Streamlit 前端界面
- 🔐 JWT 认证 + 权限控制
- 🛡 文件上传安全校验
- ⏱ 自动监控索引
- 🐳 Docker 一键部署

## 架构

```
用户 → Streamlit 前端 → FastAPI 后端 → LangChain RAG 管道
                            ├── ChromaDB（向量存储）
                            ├── JWT 认证
                            └── DeepSeek API（LLM + Embedding）
```

## 快速开始

### 本地运行

```bash
pip install -r requirements.txt
cp .env.example .env          # 填入 DEEPSEEK_API_KEY

python -m uvicorn backend.server:app --port 8000    # 终端 1
python -m streamlit run frontend/app.py              # 终端 2
# 浏览器 → http://localhost:8501
```

### Docker 部署

```bash
docker compose up -d --build
# 前端: http://localhost:8501
# API:  http://localhost:8000/docs
```

### 自动监控

```bash
python auto_watch.py
# 把文件拖到 uploads/ 目录即自动索引
```

### 生产更新

```bash
bash update.sh
```

## 安全机制

| 层级 | 措施 |
|------|------|
| 接口认证 | JWT Token（上传/删除需登录） |
| 权限控制 | 普通用户 vs 管理员角色 |
| 文件上传 | 扩展名白名单 + 大小限制 + 目录穿越防护 |
| API Key | .env 管理，不提交 Git |
| 输入校验 | Pydantic 自动校验 + 文件名清洗 |

### 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 普通用户 | user | user123 |

## API 接口

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | /api/auth/login | 否 | 登录获取 Token |
| POST | /api/upload | 是 | 上传文档 |
| GET | /api/documents | 否 | 已索引文档列表 |
| POST | /api/chat | 否 | 同步问答 |
| POST | /api/chat/stream | 否 | SSE 流式问答 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| AI 框架 | LangChain（LCEL） |
| 向量数据库 | ChromaDB |
| LLM | DeepSeek（兼容 OpenAI SDK） |
| Embedding | BAAI/bge-small-zh（本地 90MB） |
| 认证 | JWT（python-jose） |
| 前端 | Streamlit |
| 部署 | Docker + Docker Compose |

## 项目结构

```
├── backend/
│   ├── server.py          # FastAPI 接口（含认证）
│   ├── rag_pipeline.py    # RAG 管道
│   ├── config.py          # 配置
│   ├── auth.py            # JWT 认证
│   └── security.py        # 文件上传安全
├── frontend/app.py        # Streamlit 界面
├── auto_watch.py          # 自动监控索引
├── update.sh              # 生产更新脚本
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## License

MIT
