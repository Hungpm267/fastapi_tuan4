from db import Base
from sqlalchemy import Integer, Column, String, Table
from typing import Optional
from sqlalchemy import Column, Integer, String, ForeignKey
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.orm import relationship, declared_attr

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
    
# class Category(Base):
#     __tablename__ = "Categories"
    
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, unique=True, index = True)  
#     image_url = Column(String, nullable=True)
#     # --- Quan hệ cha-con ---
#     parent_id = Column(Integer, ForeignKey("Categories.id"), nullable=True) # Foreign key trỏ đến chính bảng này

#     # relationship để truy cập Category cha
#     # remote_side=[id] cần thiết cho quan hệ self-referential
#     parent = relationship("Category", back_populates="children", remote_side=[id])

#     # relationship để truy cập danh sách các Category con
#     children = relationship("Category", back_populates="parent")
    
# --- BẢNG TRUNG GIAN (ASSOCIATION TABLE) ---
# Cách tốt nhất để định nghĩa bảng trung gian cho M-2-M
# là dùng 'Table' thay vì một 'model'.
# Nó không cần class riêng vì nó không chứa dữ liệu gì
# khác ngoài 2 khóa ngoại.

product_category_table = Table(
    "middleTableProductCategory",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("Products.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("Categories.id"), primary_key=True)
)

class Product(Base):
    __tablename__ = "Products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    stock_quantity = Column(Integer, nullable=False)
    
    # Quan hệ Một-Nhiều (One-to-Many) với ProductImage
    images = relationship("ProductImage", back_populates="product")
    
    # --- QUAN HỆ NHIỀU-NHIỀU (MANY-TO-MANY) ---
    categories = relationship(
        "Category",                  # <--- Tên class Model để liên kết
        secondary=product_category_table, # <--- Tên Bảng trung gian
        back_populates="products"    # <--- Tên thuộc tính ở class Category
    )

    
class ProductImage(Base):
    __tablename__ = "ProductImage"
    
    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String, nullable=True)
    product_id = Column(Integer, ForeignKey("Products.id"), nullable=False)

    # Quan hệ ngược lại (Many-to-One)
    product = relationship("Product", back_populates="images")


class Category(Base):
    __tablename__ = "Categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index = True)  
    image_url = Column(String, nullable=True)
    parent_id = Column(Integer, ForeignKey("Categories.id"), nullable=True) 

    # Quan hệ cha-con (tự tham chiếu)
    parent = relationship("Category", back_populates="children", remote_side=[id])
    children = relationship("Category", back_populates="parent")
    
    # --- QUAN HỆ NHIỀU-NHIỀU (MANY-TO-MANY) ---
    products = relationship(
        "Product",                   # <--- Tên class Model để liên kết
        secondary=product_category_table, # <--- Dùng LẠI tên Bảng trung gian
        back_populates="categories"    # <--- Tên thuộc tính ở class Product
    )
     
    
    
    
    
    
    
    
    
    
    
# Tác dụng chính: Định nghĩa cấu trúc của bảng trong cơ sở dữ liệu (database).