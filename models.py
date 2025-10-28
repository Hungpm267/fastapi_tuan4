from db import Base
from sqlalchemy import Integer, Column, String

class Book(Base):
    __tablename__ = "Books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index = True)
    description = Column(String, index = True)
    author = Column(String, index = True)
    year = Column(Integer)
    # --- THÊM CLASS NÀY ---
class User(Base):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True, index=True)
    # Chúng ta sẽ dùng email làm username
    email = Column(String, unique=True, index=True, nullable=False) 
    # Mật khẩu đã được băm
    hashed_password = Column(String, nullable=False)
    
class Category(Base):
    __tablename__ = "Categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index = True)
    # parent = Column(Category, unique=True)    
    image_url = Column(String, nullable=True)
    
    
    
    
    
    
    
    
    
    
    
# Tác dụng chính: Định nghĩa cấu trúc của bảng trong cơ sở dữ liệu (database).