

# --- IMPORT MỚI ---
from fastapi.security import OAuth2PasswordRequestForm # Thêm class này
from datetime import timedelta # Thêm timedelta
import services, models, schemas, auth # <-- Thêm auth
from db import get_db, engine, create_table

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # <--- SỬA DÒNG NÀY
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from config import settings # <-- Import cấu hình
from jinja2 import Environment, FileSystemLoader # <-- Import Jinja2
import datetime

from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile # Thêm File, UploadFile
from fastapi.staticfiles import StaticFiles # Thêm StaticFiles
from fastapi.responses import JSONResponse # Thêm JSONResponse (tùy chọn)


# --- Cấu hình Scheduler ---
# DÒNG SỬA 2: Thay thế tên class
scheduler = AsyncIOScheduler() # <--- SỬA DÒNG NÀY

# --- Cấu hình Jinja2 ---
# Chỉ định thư mục chứa template
env = Environment(loader=FileSystemLoader("templates"))

# --- Cấu hình FastAPI-Mail ---
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD.get_secret_value(), # Lấy giá trị bí mật
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER='./templates' # Chỉ định thư mục template cho fastapi-mail (nếu cần)
)

fm = FastMail(conf)

# --- Hàm Cron Job ---
async def send_email_cron():
    """
    Hàm này sẽ được thực thi mỗi phút bởi scheduler.
    """
    print(f"Cron job running: Đang gửi email... lúc {datetime.datetime.now()}")
    
    # Lấy template
    template = env.get_template("cron_email.html")
    
    # Render template với dữ liệu
    html_body = template.render(
        time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # Người nhận (bạn có thể thay đổi)
    recipients: list[EmailStr] = ["hungmanh2607uitvnu@gmail.com"]

    message = MessageSchema(
        subject="Báo cáo Cron Job Tự Động (Mỗi 1 phút)",
        recipients=recipients,
        body=html_body,
        subtype=MessageType.html
    )

    try:
        await fm.send_message(message)
        print("-> Email đã được gửi thành công!")
    except Exception as e:
        print(f"-> Lỗi khi gửi email: {e}")

# --- Quản lý vòng đời (Lifespan) của ứng dụng ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo bảng
    print("Khởi tạo bảng cơ sở dữ liệu...")
    create_table()
    
    # Lên lịch cho cron job
    # print("Thêm cron job 'send_email_cron' chạy mỗi phút...")
    # scheduler.add_job(send_email_cron, "interval", minutes=1)
    
    # # Khởi động scheduler
    # print("Khởi động scheduler...")
    # scheduler.start()

    yield # Ứng dụng chạy ở đây

    # Tắt scheduler khi ứng dụng dừng
    print("Tắt scheduler...")
    scheduler.shutdown()

# Khởi tạo ứng dụng FastAPI với lifespan
app = FastAPI(lifespan=lifespan)

# --- THÊM CÁC ENDPOINT XÁC THỰC ---

@app.post("/signup", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def signup_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Endpoint để đăng ký user mới.
    """
    # Kiểm tra xem user đã tồn tại chưa
    db_user = services.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Tạo user mới
    return services.create_user(db=db, user=user)


@app.post("/signin", response_model=schemas.Token)
def signin_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Endpoint để đăng nhập, nhận về Access Token.
    Sử dụng form data (username & password) theo chuẩn OAuth2.
    """
    
    # 1. Lấy user từ DB (form_data.username chính là email)
    user = services.get_user_by_email(db, email=form_data.username)
    
    # 2. Kiểm tra user có tồn tại VÀ mật khẩu có đúng không
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Tạo Access Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        # "sub" (subject) là tên định danh user trong token
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )
    
    # 4. Trả về token
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    """
    Một endpoint được bảo vệ. 
    Chỉ user đã đăng nhập (cung cấp token hợp lệ) mới truy cập được.
    """
    return current_user

# --- CÁC API ENDPOINT CỦA BẠN (giữ nguyên) ---

@app.get("/books/",  response_model=list[schemas.Book])
def get_all_books(db: Session = Depends(get_db)):
    return services.get_all_book(db)



@app.get("/books/{id}", response_model=schemas.Book)
def get_book_by_id(id: int, db: Session = Depends(get_db)):
    book_queryset = services.get_book(db, id)
    if book_queryset:
        return book_queryset
    raise HTTPException(status_code=404, detail="id sach ko hop le")


@app.post("/books/", response_model=schemas.Book)
def create_new_book(book: schemas.BookCreate, 
                    db: Session=Depends(get_db), 
                    current_user: models.User = Depends(auth.get_current_user)
                    ):
    # Dòng code bên dưới chỉ chạy nếu 'get_current_user' thành công
    print(f"User {current_user.email} đang tạo sách...")
    return services.create_book(db, book)

@app.put("/books/{id}", response_model=schemas.Book)
def update_book(book: schemas.BookCreate, 
                id: int, 
                db: Session= Depends(get_db), 
                current_user: models.User = Depends(auth.get_current_user)
                ):
    db_update = services.update_book(db, book, id)
    if not db_update:
        raise HTTPException(status_code=404, detail="book not found")
    return db_update

@app.delete("/books/{id}", response_model=schemas.Book)
def delete_book(id: int, 
                db: Session=Depends(get_db), 
                current_user: models.User = Depends(auth.get_current_user) # <-- Bảo vệ
                ):
    """this api for delete a book with its id"""
    delete_entry = services.delete_book(db, id)
    if delete_entry:
        return delete_entry
    raise HTTPException(status_code=404, detail="Book not found")

# ====================CATEGORY=================
@app.get("/categories/", response_model=list[schemas.Category])
def get_all_categories(db: Session= Depends(get_db)):
    return services.get_root_category(db)

@app.get("/categories/{id}", response_model=schemas.Category)
def get_category_by_id(id: int, db: Session=Depends(get_db)):
    category_queryset = services.get_category(db, id)
    if category_queryset:
        return category_queryset
    raise HTTPException(status_code=404, detail='category ko hop le')

@app.post("/categories/", response_model=schemas.Category)
def create_new_category(category: schemas.CategoryCreate,
                        db: Session=Depends(get_db),
                        current_user: models.Category=Depends(auth.get_current_user)
                        ):
    print(f"user {current_user} is creating new category...")
    return services.create_category(db, category)

@app.put("/categories/{id}", response_model= schemas.Category)
def update_category(category: schemas.CategoryCreate,
                    id: int,
                    db: Session = Depends(get_db),
                    current_user: models.User = Depends(auth.get_current_user)
                    ):
    db_update = services.update_category(db, category, id)
    if not db_update:
        raise HTTPException(status_code=404, detail="category not found")
    return db_update
        
@app.delete("/categories/{id}", response_model=schemas.Category)
def delete_category(id: int,
                    db: Session=Depends(get_db),
                    current_user: models.User = Depends(auth.get_current_user)
                    ):
    delete_entry = services.delete_category(db, id)
    if delete_entry:
        return delete_entry
    raise HTTPException(status_code=404, detail="category not found")

# --- THÊM ENDPOINT UPLOAD ẢNH CATEGORY ---
@app.post("/categories/{category_id}/upload-image/", response_model=schemas.Category)
async def upload_category_image(
    category_id: int,
    file: UploadFile = File(...), # Nhận file upload
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(auth.get_current_user) # Bật nếu cần xác thực
):
    """
    Upload ảnh cho một Category theo ID.
    """
    try:
        updated_category = await services.save_category_image(db=db, category_id=category_id, file=file)

        # Tạo URL đầy đủ cho ảnh để trả về (tùy chọn)
        # Giả sử server chạy tại http://localhost:8000
        # Bạn có thể lấy base URL từ request nếu cần linh động hơn
        base_url = "http://localhost:8000" # Hoặc lấy từ request
        image_full_url = f"{base_url}/static/{updated_category.image_path}" if updated_category.image_path else None

        # Tạo response dictionary thủ công để thêm image_url
        response_data = schemas.Category.model_validate(updated_category).model_dump()
        response_data["image_url"] = image_full_url

        return JSONResponse(content=response_data)
        # Hoặc trả về trực tiếp nếu schema Category đã có image_url và bạn xử lý nó trong service/model
        # return updated_category

    except HTTPException as e:
        # Ném lại lỗi HTTP đã được xử lý trong service
        raise e
    except Exception as e:
        # Bắt các lỗi không mong muốn khác
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")
        
        
# ====================PRODUCT=================

# ====================PRODUCT=================

@app.post("/products/", response_model=schemas.Product)
def create_new_product(product: schemas.ProductCreate,
                       db: Session = Depends(get_db),
                       current_user: models.User = Depends(auth.get_current_user)
                       ):
    """
    Tạo sản phẩm mới và liên kết với các category IDs.
    """
    return services.create_product(db, product)
    
@app.get("/products/", response_model=list[schemas.Product])
def get_all_products(db: Session = Depends(get_db)):
    """
    Lấy tất cả sản phẩm.
    """
    return services.get_all_products(db)

@app.get("/products/{id}", response_model=schemas.Product)
def get_product_by_id(id: int, db: Session = Depends(get_db)):
    """
    Lấy một sản phẩm theo ID VÀ TĂNG LƯỢT XEM.
    """
    product_queryset = services.get_product(db, id)
    
    if not product_queryset:
        raise HTTPException(status_code=404, detail='product ko hop le')

    # --- THÊM LOGIC TĂNG LƯỢT XEM ---
    # Tăng lượt xem lên 1
    product_queryset.view_count += 1
    
    # Lưu thay đổi vào CSDL
    db.commit()
    
    # Làm mới (refresh) để đảm bảo dữ liệu trả về là mới nhất
    db.refresh(product_queryset)
    # ----------------------------------
    
    return product_queryset

# --- THÊM ENDPOINT MỚI NÀY ---
@app.post("/products/{product_id}/upload-image/", response_model=schemas.ProductImage)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user) # Bảo vệ endpoint
):
    """
    Upload một ảnh cho sản phẩm.
    Bạn có thể gọi endpoint này nhiều lần để upload nhiều ảnh.
    Ảnh đầu tiên sẽ tự động được đặt làm thumbnail của sản phẩm.
    """
    try:
        # Gọi hàm service xử lý tất cả logic
        return await services.save_product_image(db=db, product_id=product_id, file=file)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")
# ... (Endpoint create_new_product và get_product_by_id giữ nguyên) ...
    
@app.get("/products/", response_model=list[schemas.Product])
def get_all_products(
    db: Session = Depends(get_db),
    skip: int = 0,  # <-- Thêm dòng này
    limit: int = 10 # <-- Thêm dòng này
):
    """
    Lấy tất cả sản phẩm (có phân trang).
    
    Cách dùng:
    - /products/              (Lấy trang 1 - 10 sản phẩm đầu)
    - /products/?skip=0&limit=10 (Lấy trang 1)
    - /products/?skip=10&limit=10 (Lấy trang 2)
    - /products/?skip=20&limit=10 (Lấy trang 3)
    """
    # Sửa lại dòng này
    return services.get_all_products(db, skip=skip, limit=limit)
