"""RAG 问答 API — 管理员上传/删除，所有用户可问答。"""
import json, shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.chat_history import ChatHistory
from app.services import rag_service
from app.api.client.deps import get_current_user, require_admin
from app.models.user import User

router = APIRouter()
UPLOAD_DIR = Path("uploads"); UPLOAD_DIR.mkdir(exist_ok=True)

class AskRequest(BaseModel): question: str

# --- 管理员：上传 ---
@router.post("/upload")
async def upload(files: list[UploadFile] = File(...), admin: User = Depends(require_admin)):
    total = 0
    for f in files:
        if not f.filename: continue
        path = UPLOAD_DIR / f.filename
        with open(path, "wb") as fh: shutil.copyfileobj(f.file, fh)
        total += rag_service.index_file(str(path))
    return {"code": 200, "message": f"已索引 {total} 块", "total_chunks": rag_service.get_documents()["chunks"]}

# --- 管理员：删除 ---
@router.delete("/documents/{filename}")
async def delete_document(filename: str, admin: User = Depends(require_admin)):
    (UPLOAD_DIR / filename).unlink(missing_ok=True)
    rag_service.remove_document(filename)
    return {"code": 200, "message": f"已删除 {filename}"}

# --- 所有人：查看文档列表 ---
@router.get("/documents")
def documents():
    return {"code": 200, "data": rag_service.get_documents()}

# --- 所有人：问答 ---
@router.post("/ask")
async def ask_question(req: AskRequest, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if rag_service.get_documents()["chunks"] == 0:
        return {"code": 400, "message": "知识库为空，请联系管理员上传文档"}
    answer = rag_service.ask(req.question)
    db.add(ChatHistory(username=user.username if user else "anonymous", question=req.question, answer=answer[:500]))
    await db.commit()
    return {"code": 200, "data": {"answer": answer}}

# --- 所有人：流式问答 ---
@router.post("/ask/stream")
async def ask_stream(req: AskRequest, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if rag_service.get_documents()["chunks"] == 0:
        def e(): yield f"data: {json.dumps({'error':'知识库为空'})}\n\n"
        return StreamingResponse(e(), media_type="text/event-stream")
    full = ""
    async def g():
        nonlocal full
        async for text in rag_service.ask_stream(req.question):
            full += text
            yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
        db.add(ChatHistory(username=user.username if user else "anonymous", question=req.question, answer=full[:500]))
        await db.commit()
    return StreamingResponse(g(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})
