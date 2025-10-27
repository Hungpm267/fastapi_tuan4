from models import Book
from sqlalchemy.orm import Session
from schemas import BookCreate

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