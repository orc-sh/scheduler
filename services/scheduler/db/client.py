from sqlalchemy.orm import sessionmaker
from db.engine import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def client():  
    db = SessionLocal()  
    try:  
        yield db  
    finally:  
        db.close()  