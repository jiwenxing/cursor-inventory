from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Customer, User
from app.schemas import CustomerCreate, CustomerUpdate, CustomerResponse, PaginatedCustomersResponse
from app.utils import get_current_user
from app.timezone import to_cst_datetime

router = APIRouter()

@router.get("/", response_model=PaginatedCustomersResponse)
def get_customers(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    customers = db.query(Customer).offset(skip).limit(limit).all()
    total = db.query(Customer).count()
    items = [{
        "id": c.id,
        "name": c.name,
        "contact": c.contact,
        "phone": c.phone,
        "email": c.email,
        "address": c.address,
        "created_at": to_cst_datetime(c.created_at)
    } for c in customers]
    return {"items": items, "total": total}

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    return {
        "id": customer.id,
        "name": customer.name,
        "contact": customer.contact,
        "phone": customer.phone,
        "email": customer.email,
        "address": customer.address,
        "created_at": to_cst_datetime(customer.created_at)
    }

@router.post("/", response_model=CustomerResponse)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_customer = Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return {
        "id": db_customer.id,
        "name": db_customer.name,
        "contact": db_customer.contact,
        "phone": db_customer.phone,
        "email": db_customer.email,
        "address": db_customer.address,
        "created_at": to_cst_datetime(db_customer.created_at)
    }

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
    return {
        "id": db_customer.id,
        "name": db_customer.name,
        "contact": db_customer.contact,
        "phone": db_customer.phone,
        "email": db_customer.email,
        "address": db_customer.address,
        "created_at": to_cst_datetime(db_customer.created_at)
    }

@router.delete("/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    db.delete(db_customer)
    db.commit()
    return {"message": "删除成功"}
