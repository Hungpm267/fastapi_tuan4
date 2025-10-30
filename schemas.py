# schemas.py

from sqlalchemy import Column, Integer, String, ForeignKey
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List  # <-- Đảm bảo 'List' đã được import

# --- CÁC SCHEMAS CỦA BẠN (giữ nguyên) ---

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
    
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: EmailStr | None = None
    

# ===================================================================
# --- BẮT ĐẦU PHẦN MỚI ---
# ===================================================================

# --- 1. SCHEMAS CHO PRODUCT IMAGE ---
# (Định nghĩa cái này trước, vì Product sẽ dùng nó)

class ProductImageBase(BaseModel):
    # image_url sẽ được trả về từ server
    image_url: str

class ProductImage(ProductImageBase):
    id: int
    product_id: int # Thêm trường này để biết nó thuộc về SP nào
    
    model_config = ConfigDict(from_attributes=True)


# --- 2. SCHEMAS CHO PRODUCT ---

class ProductBase(BaseModel):
    name: str
    description: str
    price: int
    stock_quantity: int
    # Thêm trường thumbnail (sẽ được set ở service)
    thumbnail_url: Optional[str] = None 

class ProductCreate(ProductBase):
    # SỬA LỖI: Kế thừa từ ProductBase, không phải CategoryBase
    
    # Khi tạo sản phẩm, chúng ta muốn nhận
    # một danh sách các ID của Category để liên kết
    categories: List[int] = [] 
    
# kiểu dữ liệu typehint theo 1 công thưc chung: tên_trường: Kiểu_Dữ_Liệu = Giá_Trị_Mặc_Định

class Product(ProductBase):
    # --- THÊM DÒNG NÀY ---
    view_count: int
    # -----------------------
    id: int
    
    # --- Hiển thị các mối quan hệ ---
    
    # 1. Hiển thị danh sách các ảnh (từ 'images' trong model)
    # Pydantic sẽ tự động dùng schema 'ProductImage'
    images: List[ProductImage] = []
    
    # 2. Hiển thị danh sách các category (từ 'categories' trong model)
    # Cần dùng Forward Ref "Category" vì class Category 
    # được định nghĩa ở bên dưới
    categories: List["Category"] = []
    
    model_config = ConfigDict(from_attributes=True)


# --- 3. CẬP NHẬT SCHEMAS CHO CATEGORY ---
    
class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    parent_id: Optional[int] = None

class Category(CategoryBase):
    id: int
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    
    # Giữ nguyên quan hệ cha-con
    children: List["Category"] = []
    
    # --- THÊM MỚI ---
    # Hiển thị danh sách các sản phẩm thuộc category này
    # Cần dùng Forward Ref "Product" vì nó ở trên
    products: List[Product] = [] 
    # Lưu ý: Chúng ta dùng List[Product] thay vì List["Product"]
    # vì class Product đã được định nghĩa ở trên.
    
    model_config = ConfigDict(from_attributes=True)
    

# --- 4. CÁC LỆNH REBUILD (QUAN TRỌNG) ---
# Vì 'Category' tham chiếu đến chính nó (children)
# và 'Product' tham chiếu đến 'Category'
# Chúng ta cần gọi 'model_rebuild()' cho cả hai
# sau khi TẤT CẢ đã được định nghĩa.

Category.model_rebuild()
Product.model_rebuild()