# from models import Book
# from sqlalchemy.orm import Session
# from schemas import BookCreate
# services.py
from models import Book, User, Category, Product, ProductImage
from schemas import BookCreate, UserCreate, CategoryCreate, ProductCreate
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
import auth # <-- Import file auth mới
import shutil
import os
from PIL import Image # <-- Import thư viện Pillow
import secrets # <-- Dùng để tạo tên file ngẫu nhiên, an toàn

# ... (các import khác)

# --- THÊM CÁC ĐƯỜNG DẪN MỚI ---
UPLOAD_DIRECTORY_FULL = "static/images/products/full"
UPLOAD_DIRECTORY_THUMB = "static/images/products/thumbs"
THUMBNAIL_SIZE = (300, 300) # Kích thước thumbnail (300x300 px)

# Tạo các thư mục nếu chúng chưa tồn tại
os.makedirs(UPLOAD_DIRECTORY_FULL, exist_ok=True)
os.makedirs(UPLOAD_DIRECTORY_THUMB, exist_ok=True)

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

# THÊM HÀM NÀY:
def get_root_categories(db: Session):
    """
    Chỉ lấy các category gốc (không có cha).
    Các 'children' sẽ được tự động tải nhờ 'relationship'
    """
    return db.query(Category).filter(Category.parent_id == None).all()

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

async def save_category_image(db: Session, category_id: int, file: UploadFile) -> Category:
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
    db_category.image_url = relative_path
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


# ===================================================================
# --- BẮT ĐẦU CÁC HÀM CHO PRODUCT ---
# ===================================================================

def get_product(db: Session, product_id: int) -> Product | None:
    """Lấy một sản phẩm bằng ID."""
    return db.query(Product).filter(Product.id == product_id).first()

def get_all_products(db: Session, skip: int = 0, limit: int = 10):
    """
    Lấy tất cả sản phẩm VỚI PHÂN TRANG.
    """
    # Sửa lại hàm này
    # return db.query(Product).all() # <-- Bỏ dòng cũ
    
    # --- THAY BẰNG DÒNG NÀY ---
    return db.query(Product).offset(skip).limit(limit).all()

def create_product(db: Session, data: ProductCreate) -> Product:
    """
    Tạo một sản phẩm mới và liên kết nó với các category.
    """
    
    # 1. Tách 'categories' (list[int]) ra khỏi data
    #    dùng .pop() để lấy ra và xóa khỏi dict
    category_ids = data.model_dump().pop("categories", [])
    
    # 2. Lấy data còn lại (name, price...) để tạo Product
    #    (Vì 'categories' không phải là cột trong bảng Product)
    product_data = data.model_dump(exclude={"categories"})
    
    # 3. Tạo instance Product
    product_instance = Product(**product_data)
    
    # 4. Tìm các đối tượng Category từ list ID
    if category_ids:
        # Truy vấn tất cả Category có ID nằm trong list 'category_ids'
        categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
        
        # 5. Gắn các đối tượng Category vào sản phẩm
        #    Đây là "ảo thuật" của relationship:
        #    SQLAlchemy sẽ tự động tạo các hàng
        #    trong bảng 'middleTableProductCategory'
        product_instance.categories = categories
    
    # 6. Lưu sản phẩm vào DB
    db.add(product_instance)
    db.commit()
    db.refresh(product_instance)
    
    return product_instance


def _create_thumbnail(original_path: str, thumb_path: str, size: tuple):
    """
    Hàm nội bộ (private) để tạo thumbnail từ ảnh gốc.
    """
    try:
        with Image.open(original_path) as img:
            img.thumbnail(size) # <-- Phương thức 'thumbnail' của Pillow
            img.save(thumb_path)
    except IOError as e:
        print(f"Không thể tạo thumbnail cho {original_path}. Lỗi: {e}")
        # Xử lý lỗi (ví dụ: log lại)

async def save_product_image(db: Session, product_id: int, file: UploadFile) -> ProductImage:
    """
    Lưu ảnh cho sản phẩm, tạo thumbnail, và cập nhật thumbnail cho Product
    nếu đây là ảnh đầu tiên.
    """
    
    # 1. Kiểm tra sản phẩm có tồn tại không
    db_product = get_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # 2. Tạo tên file ngẫu nhiên và an toàn
    #    Ví dụ: 8a3f2b... .jpg
    file_extension = os.path.splitext(file.filename)[1]
    random_hex = secrets.token_hex(16)
    file_name = random_hex + file_extension
    
    # 3. Định nghĩa các đường dẫn (paths)
    full_path_on_disk = os.path.join(UPLOAD_DIRECTORY_FULL, file_name)
    thumb_path_on_disk = os.path.join(UPLOAD_DIRECTORY_THUMB, file_name)
    
    # Đường dẫn tương đối để lưu vào DB (dùng / thay vì \ )
    relative_path_full = os.path.join("images", "products", "full", file_name).replace("\\", "/")
    relative_path_thumb = os.path.join("images", "products", "thumbs", file_name).replace("\\", "/")

    # 4. Lưu ảnh gốc (bất đồng bộ)
    try:
        with open(full_path_on_disk, "wb") as buffer:
            while content := await file.read(1024):
                buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")
    finally:
        await file.close()

    # 5. Tạo thumbnail (đồng bộ, vì Pillow không hỗ trợ async)
    #    Việc này nhanh nên có thể chấp nhận được
    _create_thumbnail(full_path_on_disk, thumb_path_on_disk, THUMBNAIL_SIZE)

    # 6. Tạo record trong DB cho ảnh mới
    db_image = ProductImage(
        image_url=relative_path_full, # Lưu đường dẫn ảnh GỐC
        product_id=product_id
    )
    db.add(db_image)
    
    # 7. Cập nhật thumbnail cho Product (nếu chưa có)
    if not db_product.thumbnail_url:
        db_product.thumbnail_url = relative_path_thumb # Lưu đường dẫn THUMBNAIL
    
    db.commit()
    db.refresh(db_image)
    
    return db_image


# Tác dụng chính: Chứa logic nghiệp vụ (business logic) hay còn gọi là các hàm CRUD (Create, Read, Update, Delete).