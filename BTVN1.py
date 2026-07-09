from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

# Giả lập setup DB
Base = declarative_base()

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String)

app = FastAPI()

# Schema để trả về dữ liệu
class StudentResponse(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True

# --- HÀM SERVICE ---
def delete_student_service(db: Session, student_id: int):
    # 1. Tìm học viên
    student = db.query(Student).filter(Student.id == student_id).first()
    
    # 2. Xử lý nếu không tồn tại
    if not student:
        raise HTTPException(status_code=404, detail="Học viên không tồn tại trong hệ thống")
    
    # 3. Lưu lại thông tin trước khi xóa
    student_data = student
    
    # 4. Thực hiện xóa
    db.delete(student)
    
    # 5. Commit
    db.commit()
    
    return student_data

# --- API ENDPOINT ---
@app.delete("/students/{student_id}", response_model=dict)
def delete_student(student_id: int, db: Session = Depends(get_db)): # get_db là dependency lấy session
    deleted_student = delete_student_service(db, student_id)
    
    return {
        "message": "Xóa học viên thành công",
        "data": deleted_student
    }