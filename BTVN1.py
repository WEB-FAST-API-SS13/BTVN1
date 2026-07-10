from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional, List, Any

# 1. Cấu hình Database (Giả định sử dụng SQLite cho đơn giản, thay bằng MySQL theo yêu cầu)
SQLALCHEMY_DATABASE_URL = "sqlite:///./menu_items.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. SQLAlchemy Model
class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dish_code = Column(String(50), unique=True, nullable=False, index=True)
    dish_name = Column(String(100), nullable=False)
    calorie_count = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(30), default="AVAILABLE", nullable=False)

Base.metadata.create_all(bind=engine)

# 3. Pydantic Schemas
class MenuItemBase(BaseModel):
    dish_code: str
    dish_name: str
    calorie_count: int = Field(gt=0)
    price: float = Field(gt=0)
    status: str = "AVAILABLE"

    @field_validator("status")
    def validate_status(cls, v):
        if v not in ["AVAILABLE", "OUT_OF_STOCK"]:
            raise ValueError("status phải là AVAILABLE hoặc OUT_OF_STOCK")
        return v

class MenuItemCreate(MenuItemBase): pass

class MenuItemResponse(MenuItemBase):
    id: int
    class Config:
        from_attributes = True

# 4. Cấu trúc Response chuẩn
def create_response(status_code: int, message: str, data: Any = None, error: str = None, path: str = ""):
    return {
        "statusCode": status_code,
        "message": message,
        "error": error,
        "data": data,
        "path": path,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# 5. App & CRUD API
app = FastAPI()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.post("/menu-items")
def create_item(item: MenuItemCreate, db: Session = next(get_db())):
    try:
        new_item = MenuItem(**item.model_dump())
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return create_response(201, "Thêm món ăn thành công", new_item, path="/menu-items")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/menu-items")
def get_all(db: Session = next(get_db())):
    items = db.query(MenuItem).all()
    return create_response(200, "Lấy danh sách thành công", items, path="/menu-items")

@app.get("/menu-items/{item_id}")
def get_one(item_id: int, db: Session = next(get_db())):
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        return create_response(404, "Menu item not found", error="Not Found", path=f"/menu-items/{item_id}")
    return create_response(200, "Lấy thông tin thành công", item, path=f"/menu-items/{item_id}")

@app.put("/menu-items/{item_id}")
def update_item(item_id: int, item_data: MenuItemCreate, db: Session = next(get_db())):
    try:
        item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
        if not item:
            return create_response(404, "Menu item not found", error="Not Found", path=f"/menu-items/{item_id}")
        
        for key, value in item_data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
            
        db.commit()
        db.refresh(item)
        return create_response(200, "Cập nhật món ăn thành công", item, path=f"/menu-items/{item_id}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/menu-items/{item_id}")
def delete_item(item_id: int, db: Session = next(get_db())):
    try:
        item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
        if not item:
            return create_response(404, "Menu item not found", error="Not Found", path=f"/menu-items/{item_id}")
        db.delete(item)
        db.commit()
        return create_response(200, "Xóa món ăn thành công", path=f"/menu-items/{item_id}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
