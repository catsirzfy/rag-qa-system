"""RAG 服务 — 文档索引 + 混合检索（BM25 + 向量）+ Cross-encoder 重排序 + 问答。"""
import os
import ssl
from pathlib import Path

import jieba
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from app.core.config import settings

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_OFFLINE"] = "1"          # 强制走本地缓存，避免加载时联网卡住
os.environ["TRANSFORMERS_OFFLINE"] = "1"
ssl._create_default_https_context = ssl._create_unverified_context

# --- 基础组件 ---
llm = ChatOpenAI(model=settings.DEEPSEEK_MODEL, api_key=settings.DEEPSEEK_API_KEY,
                 base_url=settings.DEEPSEEK_BASE_URL, temperature=0.3, streaming=True)
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5", model_kwargs={"device": "cpu"})
vectorstore = Chroma(persist_directory=settings.CHROMA_PERSIST_DIR, embedding_function=embeddings)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
reranker = CrossEncoder("BAAI/bge-reranker-base", max_length=512, device="cpu")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个知识库问答助手。严格根据文档内容回答。如果文档中没有相关信息，如实告知。"),
    ("user", "文档：\n{context}\n\n问题：{question}"),
])

# --- 混合检索状态：BM25 索引建立在全量分块上，文档增删后重建 ---
_all_docs: list[Document] = []
_bm25: BM25Okapi | None = None


def _refresh_bm25() -> None:
    """从 ChromaDB 拉取全量分块，重建 BM25 关键词索引。"""
    global _all_docs, _bm25
    data = vectorstore._collection.get()
    docs = data.get("documents") or []
    metas = data.get("metadatas") or [{}] * len(docs)
    _all_docs = [Document(page_content=d, metadata=m) for d, m in zip(docs, metas)]
    _bm25 = BM25Okapi([jieba.lcut(d) for d in docs]) if docs else None


def index_file(path: str) -> int:
    p = Path(path)
    ext = p.suffix.lower()
    loader = TextLoader(str(p), encoding="utf-8") if ext in (".md", ".txt") else PyPDFLoader(str(p))
    docs = loader.load()
    for d in docs:
        d.metadata["source"] = p.name
    chunks = text_splitter.split_documents(docs)
    vectorstore.add_documents(chunks)
    _refresh_bm25()
    return len(chunks)


def get_documents() -> dict:
    try:
        m = vectorstore._collection.get()["metadatas"]
    except Exception:
        return {"files": [], "chunks": 0}
    sources = sorted(set(str(x["source"]) for x in m if x and "source" in x))
    return {"files": sources, "chunks": vectorstore._collection.count() if vectorstore._collection else 0}


def remove_document(filename: str) -> bool:
    """从 ChromaDB 删除某个文件的所有文档块。"""
    try:
        results = vectorstore._collection.get()
        if not results["ids"]:
            return False
        ids_to_delete = [
            rid for rid, meta in zip(results["ids"], results["metadatas"])
            if meta and meta.get("source") == filename
        ]
        if ids_to_delete:
            vectorstore._collection.delete(ids=ids_to_delete)
            _refresh_bm25()
            return True
        return False
    except Exception:
        return False


def _hybrid_search(question: str, top_k: int = 10) -> list[Document]:
    """向量检索 + BM25 关键词检索，用 RRF（倒数排名融合）排序。"""
    if _bm25 is None:
        _refresh_bm25()

    vec_docs = vectorstore.similarity_search(question, k=top_k)
    if _bm25 is None:
        return vec_docs

    # BM25 打分，取 top_k
    scores = _bm25.get_scores(jieba.lcut(question))
    order = sorted(range(len(scores)), key=lambda i: -scores[i])[:top_k]
    bm25_docs = [_all_docs[i] for i in order]

    # RRF 融合：两个通道各自排名，按 1/(60+rank) 累加（60 是经验常数，降低名次敏感度）
    fused_score: dict[str, float] = {}
    fused_doc: dict[str, Document] = {}
    for rank, d in enumerate(vec_docs):
        fused_score[d.page_content] = fused_score.get(d.page_content, 0.0) + 1.0 / (60 + rank)
        fused_doc[d.page_content] = d
    for rank, d in enumerate(bm25_docs):
        fused_score[d.page_content] = fused_score.get(d.page_content, 0.0) + 1.0 / (60 + rank)
        fused_doc[d.page_content] = d

    ranked = sorted(fused_score.items(), key=lambda x: -x[1])
    return [fused_doc[c] for c, _ in ranked]


def _rerank(question: str, docs: list[Document], top_n: int = 4) -> list[Document]:
    """Cross-encoder 对候选集精排：逐条算 (问题, 分块) 相关度，取 top_n。"""
    if not docs:
        return docs
    pairs = [(question, d.page_content) for d in docs]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(docs, scores), key=lambda x: -x[1])
    return [d for d, _ in ranked[:top_n]]


def _retrieve(question: str, top_k: int = 10, top_n: int = 4) -> list[Document]:
    """混合检索（粗排）→ Cross-encoder 重排序（精排）。"""
    return _rerank(question, _hybrid_search(question, top_k), top_n)


def _fmt(docs: list[Document]) -> str:
    return "\n\n---\n\n".join(f"[{d.metadata.get('source', '?')}] {d.page_content}" for d in docs)


def ask(question: str) -> str:
    docs = _retrieve(question)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context": _fmt(docs), "question": question})


async def ask_stream(question: str):
    docs = _retrieve(question)
    chain = prompt | llm | StrOutputParser()
    async for chunk in chain.astream({"context": _fmt(docs), "question": question}):
        yield chunk
