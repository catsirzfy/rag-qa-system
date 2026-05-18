"""文档记录模型。"""
from sqlalchemy import Column, String, Integer
from app.models.base import BaseModel

class Document(BaseModel):
    __tablename__ = "documents"
    filename = Column(String(500), nullable=False)
    file_type = Column(String(20))
    chunks_count = Column(Integer, default=0)
    uploaded_by = Column(String(100))  # 上传者用户名
