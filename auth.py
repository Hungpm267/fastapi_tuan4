# auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext

import schemas, services, models
from db import get_db
from config import settings

# 1. Cấu hình Passlib (dùng để băm mật khẩu)
# Chúng ta chọn bcrypt làm thuật toán băm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. Cấu hình OAuth2
# "tokenUrl" trỏ đến endpoint /signin (chúng ta sẽ tạo ở main.py)
# Client sẽ gửi username/password đến URL này để lấy token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/signin")

# 3. Các hàm xử lý mật khẩu
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu thô có khớp với mật khẩu đã băm không."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Băm mật khẩu."""
    return pwd_context.hash(password)

# 4. Các hàm xử lý JWT
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Tạo ra một JWT Access Token mới."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Mặc định token hết hạn sau 15 phút nếu không truyền
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    
    # Lấy SECRET_KEY từ config và encode
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY.get_secret_value(), 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

# 5. Hàm quan trọng: Lấy user hiện tại từ Token
async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    """
    Giải mã token, lấy email từ payload, và truy vấn user từ DB.
    Đây là Dependency sẽ được dùng để bảo vệ các endpoint.
    """
    
    # Thông tin lỗi chuẩn
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Giải mã JWT
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM]
        )
        
        # Lấy email từ payload (chúng ta đã đặt nó trong "sub")
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
            
        # Validate schema của payload
        token_data = schemas.TokenData(email=email)
        
    except JWTError:
        # Nếu token không hợp lệ hoặc hết hạn
        raise credentials_exception
    
    # Lấy user từ DB
    user = services.get_user_by_email(db, email=token_data.email)
    
    if user is None:
        # Nếu user không tồn tại trong DB (ví dụ: user đã bị xóa)
        raise credentials_exception
        
    # Trả về instance User (model của SQLAlchemy)
    return user