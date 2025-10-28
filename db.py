from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://hung:hung@localhost:5432/book_fastapi"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind = engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db 
    finally: 
        db.close()
        
def create_table():
    Base.metadata.create_all(bind = engine)
    
    
    
    
    
    
    
    
    
    
    # Tác dụng chính: Quản lý việc kết nối và phiên làm việc (session) với database.