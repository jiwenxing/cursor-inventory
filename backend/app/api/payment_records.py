from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import PaymentRecord, SalesOrder, User, PaymentMethod
from app.schemas import PaymentRecordCreate, PaymentRecordResponse, PaymentRecordListResponse
from app.utils import get_current_user
from app.timezone import to_cst_datetime

router = APIRouter()


def update_payment_status(order: SalesOrder, db: Session):
    """根据已付金额自动更新订单的付款状态"""
    paid_amount = db.query(func.sum(PaymentRecord.amount)).filter(
        PaymentRecord.order_id == order.id
    ).scalar() or 0

    order.paid_amount = paid_amount

    # 自动更新付款状态
    if paid_amount <= 0:
        order.payment_status = "未付款"
    elif paid_amount >= order.total_amount:
        order.payment_status = "已付款"
    else:
        order.payment_status = "部分付款"


def payment_record_to_dict(record: PaymentRecord, db: Session = None) -> dict:
    """将收款记录转换为字典"""
    order = record.order
    return {
        "id": record.id,
        "order_id": record.order_id,
        "order_no": order.id if order else None,
        "customer_name": order.customer.name if order and order.customer else None,
        "order_total_amount": order.total_amount if order else None,
        "order_paid_amount": order.paid_amount if order else None,
        "order_unpaid_amount": (order.total_amount - order.paid_amount) if order else None,
        "amount": record.amount,
        "payment_date": to_cst_datetime(record.payment_date),
        "payment_method": record.payment_method,
        "remark": record.remark,
        "created_by": record.created_by,
        "creator_name": record.creator.name if record.creator else None,
        "created_at": to_cst_datetime(record.created_at)
    }


@router.get("/", response_model=List[PaymentRecordListResponse])
def get_payment_records(
    skip: int = 0,
    limit: int = 50,
    order_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取收款记录列表"""
    query = db.query(PaymentRecord)

    # 按订单 ID 筛选
    if order_id is not None:
        query = query.filter(PaymentRecord.order_id == order_id)

    # 按日期范围筛选
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(PaymentRecord.payment_date >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(PaymentRecord.payment_date <= end)
        except ValueError:
            pass

    # 分页查询，使用 joinedload 预加载关联数据
    records = query.options(joinedload(PaymentRecord.creator), joinedload(PaymentRecord.order))\
        .order_by(PaymentRecord.payment_date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

    return [payment_record_to_dict(record, db) for record in records]


@router.get("/{record_id}", response_model=PaymentRecordResponse)
def get_payment_record(record_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取单个收款记录"""
    record = db.query(PaymentRecord).filter(PaymentRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="收款记录不存在")
    return record


@router.post("/", response_model=PaymentRecordResponse)
def create_payment_record(
    record: PaymentRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建收款记录"""
    # 验证订单存在
    order = db.query(SalesOrder).filter(SalesOrder.id == record.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 检查收款金额是否超过未付金额
    unpaid_amount = order.total_amount - (order.paid_amount or 0)
    if record.amount > unpaid_amount:
        raise HTTPException(
            status_code=400,
            detail=f"收款金额不能超过未付金额 {unpaid_amount:.2f} 元"
        )

    # 创建收款记录
    db_record = PaymentRecord(
        order_id=record.order_id,
        amount=record.amount,
        payment_date=record.payment_date,
        payment_method=record.payment_method,
        remark=record.remark,
        created_by=current_user.id
    )
    db.add(db_record)

    # 更新订单的付款状态和已付金额
    update_payment_status(order, db)

    db.commit()
    db.refresh(db_record)

    return db_record


@router.delete("/{record_id}")
def delete_payment_record(record_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除收款记录"""
    record = db.query(PaymentRecord).filter(PaymentRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="收款记录不存在")

    # 获取关联的订单
    order = record.order

    # 删除收款记录
    db.delete(record)

    # 重新计算订单的付款状态
    if order:
        update_payment_status(order, db)

    db.commit()

    return {"message": "删除成功"}


@router.get("/order/{order_id}", response_model=List[PaymentRecordListResponse])
def get_order_payment_records(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取指定订单的所有收款记录"""
    # 验证订单存在
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 使用 joinedload 预加载关联数据
    records = db.query(PaymentRecord)\
        .options(joinedload(PaymentRecord.creator), joinedload(PaymentRecord.order))\
        .filter(PaymentRecord.order_id == order_id)\
        .all()

    # 使用 payment_record_to_dict 转换，包含创建人信息
    return [payment_record_to_dict(record, db) for record in records]
