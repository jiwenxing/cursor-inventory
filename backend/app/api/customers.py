from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Customer, User
from app.schemas import CustomerCreate, CustomerUpdate, CustomerResponse
from app.utils import get_current_user

router = APIRouter()

@router.get("/", response_model=List[CustomerResponse])
def get_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    customers = db.query(Customer).offset(skip).limit(limit).all()
    return customers

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    return customer

@router.post("/", response_model=CustomerResponse)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if customer.code:
        existing = db.query(Customer).filter(Customer.code == customer.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="客户编码已存在")
    db_customer = Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, customer: CustomerUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    update_data = customer.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_customer, field, value)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.delete("/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    db.delete(db_customer)
    db.commit()
    return {"message": "删除成功"}
