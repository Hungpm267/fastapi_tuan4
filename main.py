from fastapi import FastAPI, Depends, HTTPException
import services, models, schemas
from db import get_db, engine, create_table

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # <--- SỬA DÒNG NÀY
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from config import settings # <-- Import cấu hình
from jinja2 import Environment, FileSystemLoader # <-- Import Jinja2
import datetime

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
    print("Thêm cron job 'send_email_cron' chạy mỗi phút...")
    scheduler.add_job(send_email_cron, "interval", minutes=1)
    
    # Khởi động scheduler
    print("Khởi động scheduler...")
    scheduler.start()

    yield # Ứng dụng chạy ở đây

    # Tắt scheduler khi ứng dụng dừng
    print("Tắt scheduler...")
    scheduler.shutdown()

# Khởi tạo ứng dụng FastAPI với lifespan
app = FastAPI(lifespan=lifespan)


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
def create_new_book(book: schemas.BookCreate, db: Session=Depends(get_db)):
    return services.create_book(db, book)

@app.put("/books/{id}", response_model=schemas.Book)
def update_book(book: schemas.BookCreate, id: int, db: Session= Depends(get_db)):
    db_update = services.update_book(db, book, id)
    if not db_update:
        raise HTTPException(status_code=404, detail="book not found")
    return db_update

@app.delete("/books/{id}", response_model=schemas.Book)
def delete_book(id: int, db: Session=Depends(get_db)):
    """this api for delete a book with its id"""
    delete_entry = services.delete_book(db, id)
    if delete_entry:
        return delete_entry
    raise HTTPException(status_code=404, detail="Book not found")