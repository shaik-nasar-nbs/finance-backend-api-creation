from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import engine, Base, SessionLocal
import models, schemas

app = FastAPI(title="Finance Backend API 🚀")

# Create tables
Base.metadata.create_all(bind=engine)

# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Home Route
@app.get("/")
def home():
    return {"message": "Finance Backend Running 🚀"}

# ➕ CREATE RECORD
@app.post("/records")
def create_record(record: schemas.RecordCreate, db: Session = Depends(get_db)):
    if record.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    if record.type not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="Type must be 'income' or 'expense'")

    new_record = models.FinancialRecord(**record.dict())
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

# 📥 GET ALL RECORDS
@app.get("/records")
def get_records(db: Session = Depends(get_db)):
    return db.query(models.FinancialRecord).all()

# 🔍 GET SINGLE RECORD
@app.get("/records/{record_id}")
def get_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.FinancialRecord).filter(models.FinancialRecord.id == record_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    return record

# ✏️ UPDATE RECORD
@app.put("/records/{record_id}")
def update_record(record_id: int, updated: schemas.RecordCreate, db: Session = Depends(get_db)):
    record = db.query(models.FinancialRecord).filter(models.FinancialRecord.id == record_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    for key, value in updated.dict().items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record

# ❌ DELETE RECORD
@app.delete("/records/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.FinancialRecord).filter(models.FinancialRecord.id == record_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    db.delete(record)
    db.commit()
    return {"message": "Record deleted successfully"}

# 🔍 FILTER RECORDS
@app.get("/records/filter")
def filter_records(
    type: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.FinancialRecord)

    if type:
        query = query.filter(models.FinancialRecord.type == type)

    if category:
        query = query.filter(models.FinancialRecord.category == category)

    return query.all()

# 📊 SUMMARY API
@app.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    records = db.query(models.FinancialRecord).all()

    total_income = sum(r.amount for r in records if r.type == "income")
    total_expense = sum(r.amount for r in records if r.type == "expense")

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense
    }

# 📂 CATEGORY SUMMARY
@app.get("/category-summary")
def category_summary(db: Session = Depends(get_db)):
    records = db.query(models.FinancialRecord).all()

    result = {}

    for r in records:
        if r.category not in result:
            result[r.category] = 0
        result[r.category] += r.amount

    return result

# 📅 MONTHLY SUMMARY
@app.get("/monthly-summary")
def monthly_summary(db: Session = Depends(get_db)):
    records = db.query(models.FinancialRecord).all()

    result = {}

    for r in records:
        month = r.date.strftime("%Y-%m")

        if month not in result:
            result[month] = 0

        if r.type == "income":
            result[month] += r.amount
        else:
            result[month] -= r.amount

    return result