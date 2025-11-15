from app.models.http_method import HttpMethodEnum
from sqlalchemy import JSON, Column, ForeignKey, String, Integer
from sqlalchemy.orm import relationship
from app.models.base import Base 

class Webhook(Base):  
    __tablename__ = "webhooks"  
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    url = Column(String(255), nullable=False)  
    method = Column(HttpMethodEnum, nullable=False)  
    headers = Column(JSON, nullable=True)  
    body = Column(JSON, nullable=True)  
    task = relationship("Task", uselist=False, back_populates="webhook")
    
    class Config:
        orm_mode = True