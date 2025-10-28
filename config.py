from pydantic_settings import BaseSettings
from pydantic import EmailStr, SecretStr

class Settings(BaseSettings):
    # Cấu hình cho FastAPI-Mail
    MAIL_USERNAME: str
    MAIL_PASSWORD: SecretStr
    MAIL_FROM: EmailStr
    MAIL_PORT: int = 587
    MAIL_SERVER: str
    MAIL_FROM_NAME: str = "My FastAPI App"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    
    # --- THÊM CÁC DÒNG NÀY ---
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # --------------------------
    
    class Config:
        # Tên file để tải biến môi trường
        env_file = ".env"

# Tạo một instance của Settings để import trong các file khác
settings = Settings()