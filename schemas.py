
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional


class BookBase(BaseModel):
    title: str
    author: str
    description: str
    year: int
    
class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
    
# --- THÊM CÁC SCHEMAS BÊN DƯỚI ---

# --- SCHEMAS CHO USER ---
class UserBase(BaseModel):
    email: EmailStr

# Schema để tạo user (signup) - cần mật khẩu
class UserCreate(UserBase):
    password: str

# Schema để đọc user (trả về API) - không có mật khẩu
class User(UserBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# --- SCHEMAS CHO TOKEN ---
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema cho dữ liệu bên trong token
class TokenData(BaseModel):
    email: EmailStr | None = None
    
# --- SCHEMAS CHO CATEGORY ---
    
class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    image_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
    
# Tác dụng chính: Định nghĩa hình dạng (shape) của dữ liệu cho API.