# from models import Book
# from sqlalchemy.orm import Session
# from schemas import BookCreate
# services.py
from models import Book, User, Category # <-- Thêm User
from sqlalchemy.orm import Session
from schemas import BookCreate, UserCreate, CategoryCreate # <-- Thêm UserCreate
from fastapi import UploadFile, HTTPException, status
import auth # <-- Import file auth mới
import shutil
import os

def create_book(db: Session, data: BookCreate):
    book_instance = Book(**data.model_dump())
    db.add(book_instance)
    db.commit()
    db.refresh(book_instance)
    return book_instance

def get_all_book(db: Session):
    return db.query(Book).all()
    
def get_book(db: Session, book_id: int):
    return db.query(Book).filter(Book.id == book_id).first()

def update_book(db: Session, book: BookCreate, book_id:int):
    book_queryset = db.query(Book).filter(Book.id==book_id).first()
    if book_queryset:
        for key, value in book.model_dump().items():
            setattr(book_queryset, key, value)
        db.commit()
        db.refresh(book_queryset)
    return book_queryset

def delete_book(db: Session, id: int):
    book_queryset = db.query(Book).filter(Book.id == id).first()
    if book_queryset:
        db.delete(book_queryset)
        db.commit()
        
    return book_queryset

# --- THÊM CÁC HÀM CHO Category ---
# Đường dẫn đến thư mục lưu ảnh category
UPLOAD_DIRECTORY = "static/images/categories"
# Tạo thư mục nếu chưa tồn tại
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
# ==============================
def create_category(db: Session, data: CategoryCreate):
    category_instance = Category(**data.model_dump())
    db.add(category_instance)
    db.commit()
    db.refresh(category_instance)
    return category_instance

def get_all_category(db: Session):
    return db.query(Category).all()

def get_category(db: Session, category_id: int):
    return db.query(Category).filter(Category.id == category_id).first()

def update_category(db: Session, category: CategoryCreate, category_id: int):
    category_queryset = db.query(Category).filter(Category.id == category_id).first()
    if category_queryset:
        for key, value in category.model_dump().items():
            setattr(category_queryset, key, value)
        db.commit()
        db.refresh(category_queryset)
    return category_queryset

def delete_category(db: Session, category_id: int):
    category_queryset = db.query(Category).filter(Category.id == category_id).first()
    if category_queryset:
        db.delete(category_queryset)
        db.commit()
    return category_queryset

async def save_category_image(db: Session, category_id: int, file: UploadFile) -> models.Category:
    """Lưu ảnh và cập nhật đường dẫn cho category."""
    db_category = get_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # Tạo tên file duy nhất hoặc sử dụng tên gốc (cẩn thận trùng lặp)
    # Ví dụ: dùng ID category và tên file gốc
    file_extension = os.path.splitext(file.filename)[1]
    file_name = f"{category_id}_{file.filename}" # Hoặc tạo tên an toàn hơn
    file_path = os.path.join(UPLOAD_DIRECTORY, file_name)

    # Lưu file ảnh
    try:
        with open(file_path, "wb") as buffer:
            # Đọc nội dung file upload theo chunk và ghi vào buffer
            while content := await file.read(1024): # Đọc 1KB mỗi lần
                buffer.write(content)
    except Exception as e:
        # Xử lý lỗi nếu không lưu được file
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")
    finally:
        await file.close() # Đảm bảo file được đóng

    # Cập nhật đường dẫn ảnh vào database
    # Lưu đường dẫn tương đối để dễ dàng tạo URL sau này
    relative_path = os.path.join("images", "categories", file_name).replace("\\", "/") # Đảm bảo dùng '/'
    db_category.image_path = relative_path
    db.commit()
    db.refresh(db_category)

    return db_category

# --- THÊM CÁC HÀM CHO USER ---

def get_user_by_email(db: Session, email: str) -> User | None:
    """Tìm user bằng email."""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    """Tạo user mới (cho chức năng signup)."""
    
    # Băm mật khẩu trước khi lưu
    hashed_password = auth.get_password_hash(user.password)
    
    # Tạo instance User model (chỉ lưu hashed_password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

















# Tác dụng chính: Chứa logic nghiệp vụ (business logic) hay còn gọi là các hàm CRUD (Create, Read, Update, Delete).