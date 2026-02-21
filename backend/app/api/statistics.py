from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import SalesOrder, SalesOrderItem, Customer, Product, User
from app.utils import get_current_user

router = APIRouter()

@router.get("/sales-by-customer")
def get_sales_by_customer(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(
        Customer.id,
        Customer.name,
        func.sum(SalesOrder.total_amount).label("total_amount"),
        func.count(SalesOrder.id).label("order_count")
    ).join(SalesOrder, SalesOrder.customer_id == Customer.id)
    
    if start_date:
        query = query.filter(SalesOrder.order_date >= start_date)
    if end_date:
        query = query.filter(SalesOrder.order_date <= end_date)
    
    results = query.group_by(Customer.id, Customer.name).all()
    return [
        {
            "customer_id": r.id,
            "customer_name": r.name,
            "total_amount": float(r.total_amount or 0),
            "order_count": r.order_count
        }
        for r in results
    ]

@router.get("/sales-by-product")
def get_sales_by_product(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(
        Product.id,
        Product.name,
        Product.model,
        func.sum(SalesOrderItem.quantity).label("total_quantity"),
        func.sum(SalesOrderItem.line_total).label("total_amount")
    ).join(SalesOrderItem, SalesOrderItem.product_id == Product.id)\
     .join(SalesOrder, SalesOrderItem.order_id == SalesOrder.id)
    
    if start_date:
        query = query.filter(SalesOrder.order_date >= start_date)
    if end_date:
        query = query.filter(SalesOrder.order_date <= end_date)
    
    results = query.group_by(Product.id, Product.name, Product.model).all()
    return [
        {
            "product_id": r.id,
            "product_name": r.name,
            "product_model": r.model,
            "total_quantity": float(r.total_quantity or 0),
            "total_amount": float(r.total_amount or 0)
        }
        for r in results
    ]

@router.get("/receivables")
def get_receivables(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = db.query(
        Customer.id,
        Customer.name,
        func.sum(
            func.case(
                (SalesOrder.payment_status == "未付款", SalesOrder.total_amount),
                (SalesOrder.payment_status == "部分付款", SalesOrder.total_amount * 0.5),
                else_=0
            )
        ).label("receivable_amount")
    ).join(SalesOrder, SalesOrder.customer_id == Customer.id)\
     .group_by(Customer.id, Customer.name)\
     .having(func.sum(
         func.case(
             (SalesOrder.payment_status == "未付款", SalesOrder.total_amount),
             (SalesOrder.payment_status == "部分付款", SalesOrder.total_amount * 0.5),
             else_=0
         )
     ) > 0).all()
    
    return [
        {
            "customer_id": r.id,
            "customer_name": r.name,
            "receivable_amount": float(r.receivable_amount or 0)
        }
        for r in results
    ]
