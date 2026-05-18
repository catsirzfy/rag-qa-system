"""RAG 服务 — 文档索引 + 问答。"""
import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import ssl; ssl._create_default_https_context = ssl._create_unverified_context

llm = ChatOpenAI(model=settings.DEEPSEEK_MODEL, api_key=settings.DEEPSEEK_API_KEY,
                 base_url=settings.DEEPSEEK_BASE_URL, temperature=0.3, streaming=True)
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5", model_kwargs={"device": "cpu"})
vectorstore = Chroma(persist_directory=settings.CHROMA_PERSIST_DIR, embedding_function=embeddings)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个知识库问答助手。严格根据文档内容回答。如果文档中没有相关信息，如实告知。"),
    ("user", "文档：\n{context}\n\n问题：{question}"),
])

def index_file(path: str) -> int:
    p = Path(path); ext = p.suffix.lower()
    loader = TextLoader(str(p), encoding="utf-8") if ext in (".md",".txt") else PyPDFLoader(str(p))
    docs = loader.load()
    for d in docs: d.metadata["source"] = p.name
    chunks = text_splitter.split_documents(docs)
    vectorstore.add_documents(chunks)
    return len(chunks)

def get_documents() -> dict:
    try:
        m = vectorstore._collection.get()["metadatas"]
    except: return {"files":[],"chunks":0}
    sources = sorted(set(str(x["source"]) for x in m if x and "source" in x))
    return {"files": sources, "chunks": vectorstore._collection.count() if vectorstore._collection else 0}

def remove_document(filename: str) -> bool:
    """从 ChromaDB 删除某个文件的所有文档块。"""
    try:
        results = vectorstore._collection.get()
        if not results["ids"]: return False
        ids_to_delete = [
            rid for rid, meta in zip(results["ids"], results["metadatas"])
            if meta and meta.get("source") == filename
        ]
        if ids_to_delete:
            vectorstore._collection.delete(ids=ids_to_delete)
            return True
        return False
    except Exception:
        return False

def ask(question: str) -> str:
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    def fmt(docs): return "\n\n---\n\n".join(f"[{d.metadata.get('source','?')}] {d.page_content}" for d in docs)
    chain = ({"context": retriever | fmt, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser())
    return chain.invoke(question)

async def ask_stream(question: str):
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    def fmt(docs): return "\n\n---\n\n".join(f"[{d.metadata.get('source','?')}] {d.page_content}" for d in docs)
    chain = ({"context": retriever | fmt, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser())
    async for chunk in chain.astream(question):
        yield chunk
