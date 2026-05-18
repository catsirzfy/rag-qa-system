"""对话记录模型 — 审计谁问了什么问题。"""
from sqlalchemy import Column, String, Text, Integer
from app.models.base import BaseModel

class ChatHistory(BaseModel):
    __tablename__ = "chat_history"
    username = Column(String(100), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
