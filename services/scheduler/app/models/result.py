from sqlalchemy import Column, String, Integer, DateTime, Text
from app.models.base import Base 

class TaskResult(Base):  
    __tablename__ = "results"  
    id = Column(Integer, primary_key=True, autoincrement=True)  
    task_id = Column(String(255), nullable=False)  
    status = Column(String(50), nullable=False)  
    response_status = Column(Integer, nullable=True)  
    response_body = Column(Text, nullable=True)  
    response_headers = Column(Text, nullable=True)  
    timestamp = Column(DateTime, nullable=False)  
    error = Column(Text, nullable=True)  

    class Config:
        orm_mode = True