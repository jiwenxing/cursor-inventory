from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Invoice, InvoiceItem, SalesOrder, Customer, User
from app.schemas import InvoiceCreate, InvoiceResponse, PaginatedInvoicesResponse, OrderInvoiceInfo
from app.utils import get_current_user

router = APIRouter()


def generate_invoice_no():
    """生成发票号（格式：INV + 年月日 + 4位序号）"""
    from app.models import Invoice
    today = datetime.now().strftime("%Y%m%d")
    # 查找今天最大的序号
    today_prefix = f"INV{today}"
    last_invoice = db.query(Invoice).filter(
        Invoice.invoice_no.like(f"{today_prefix}%")
    ).order_by(Invoice.invoice_no.desc()).first()

    if last_invoice:
        try:
            last_seq = int(last_invoice.invoice_no[-4:])
            new_seq = last_seq + 1
        except ValueError:
            new_seq = 1
    else:
        new_seq = 1

    return f"{today_prefix}{new_seq:04d}"


@router.get("/", response_model=PaginatedInvoicesResponse)
def get_invoices(
    skip: int = 0,
    limit: int = 15,
    customer_id: Optional[int] = None,
    invoice_no: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Invoice)

    # 按客户ID筛选
    if customer_id is not None:
        query = query.filter(Invoice.customer_id == customer_id)

    # 按发票号筛选
    if invoice_no:
        query = query.filter(Invoice.invoice_no.ilike(f"%{invoice_no}%"))

    # 按日期范围筛选
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Invoice.invoice_date >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(Invoice.invoice_date <= end)
        except ValueError:
            pass

    # 按状态筛选
    if status:
        query = query.filter(Invoice.status == status)

    # 获取总数
    total = query.count()

    # 分页查询
    invoices = query.order_by(Invoice.invoice_date.desc()).offset(skip).limit(limit).all()

    # 转换结果
    result = []
    for inv in invoices:
        result.append({
            "id": inv.id,
            "invoice_no": inv.invoice_no,
            "invoice_date": inv.invoice_date,
            "customer_id": inv.customer_id,
            "customer_name": inv.customer.name if inv.customer else None,
            "total_amount": inv.total_amount,
            "tax_amount": inv.tax_amount,
            "status": inv.status,
            "remark": inv.remark,
            "created_by": inv.created_by,
            "creator_name": inv.creator.name if inv.creator else None,
            "created_at": inv.created_at,
            "items": [{
                "id": item.id,
                "invoice_id": item.invoice_id,
                "order_id": item.order_id,
                "order_no": item.order_no,
                "amount": item.amount,
                "tax_amount": item.tax_amount
            } for item in inv.items]
        })

    return {"items": result, "total": total}


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    return {
        "id": invoice.id,
        "invoice_no": invoice.invoice_no,
        "invoice_date": invoice.invoice_date,
        "customer_id": invoice.customer_id,
        "customer_name": invoice.customer.name if invoice.customer else None,
        "total_amount": invoice.total_amount,
        "tax_amount": invoice.tax_amount,
        "status": invoice.status,
        "remark": invoice.remark,
        "created_by": invoice.created_by,
        "creator_name": invoice.creator.name if invoice.creator else None,
        "created_at": invoice.created_at,
        "items": [{
            "id": item.id,
            "invoice_id": item.invoice_id,
            "order_id": item.order_id,
            "order_no": item.order_no,
            "amount": item.amount,
            "tax_amount": item.tax_amount
        } for item in invoice.items]
    }


@router.post("/", response_model=InvoiceResponse)
def create_invoice(invoice: InvoiceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 验证客户存在
    customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 检查发票号是否已存在
    existing = db.query(Invoice).filter(Invoice.invoice_no == invoice.invoice_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="发票号已存在")

    # 验证每个订单
    total_invoiced = 0
    total_tax = 0
    for item in invoice.items:
        order = db.query(SalesOrder).filter(SalesOrder.id == item.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail=f"订单ID {item.order_id} 不存在")

        # 检查订单是否属于该客户
        if order.customer_id != invoice.customer_id:
            raise HTTPException(status_code=400, detail=f"订单 {order.id} 不属于该客户")

        # 计算该订单已开票金额
        invoiced = db.query(func.sum(InvoiceItem.amount)).filter(
            InvoiceItem.order_id == item.order_id
        ).scalar() or 0

        # 计算可开票余额
        balance = order.total_amount - invoiced

        # 检查开票金额是否超过可开票余额
        if item.amount > balance:
            raise HTTPException(status_code=400, detail=f"订单 {order.id} 开票金额超过可开票余额（{balance:.2f}）")

        total_invoiced += item.amount
        total_tax += item.tax_amount

    # 验证总金额
    if abs(total_invoiced - invoice.total_amount) > 0.01:
        raise HTTPException(status_code=400, detail="发票总金额与明细汇总不符")

    # 创建发票
    db_invoice = Invoice(
        invoice_no=invoice.invoice_no,
        invoice_date=invoice.invoice_date,
        customer_id=invoice.customer_id,
        total_amount=invoice.total_amount,
        tax_amount=invoice.tax_amount,
        remark=invoice.remark,
        created_by=current_user.id
    )
    db.add(db_invoice)
    db.flush()

    # 创建发票明细
    for item in invoice.items:
        order = db.query(SalesOrder).filter(SalesOrder.id == item.order_id).first()
        db_item = InvoiceItem(
            invoice_id=db_invoice.id,
            order_id=item.order_id,
            order_no=order.id,
            amount=item.amount,
            tax_amount=item.tax_amount
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_invoice)

    return get_invoice(db_invoice.id, db, current_user)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(invoice_id: int, invoice: InvoiceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 已作废的发票不能修改
    if db_invoice.status == "已作废":
        raise HTTPException(status_code=400, detail="已作废的发票不能修改")

    # 验证客户存在
    customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 检查发票号是否已存在（排除自身）
    existing = db.query(Invoice).filter(
        Invoice.invoice_no == invoice.invoice_no,
        Invoice.id != invoice_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="发票号已存在")

    # 删除旧的明细
    db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).delete()

    # 重新验证每个订单并创建新明细
    for item in invoice.items:
        order = db.query(SalesOrder).filter(SalesOrder.id == item.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail=f"订单ID {item.order_id} 不存在")

        if order.customer_id != invoice.customer_id:
            raise HTTPException(status_code=400, detail=f"订单 {order.id} 不属于该客户")

        # 计算该订单已开票金额（排除当前发票）
        invoiced = db.query(func.sum(InvoiceItem.amount)).filter(
            InvoiceItem.order_id == item.order_id,
            InvoiceItem.invoice_id != invoice_id
        ).scalar() or 0

        balance = order.total_amount - invoiced
        if item.amount > balance:
            raise HTTPException(status_code=400, detail=f"订单 {order.id} 开票金额超过可开票余额（{balance:.2f}）")

        db_item = InvoiceItem(
            invoice_id=db_invoice.id,
            order_id=item.order_id,
            order_no=order.id,
            amount=item.amount,
            tax_amount=item.tax_amount
        )
        db.add(db_item)

    # 更新发票
    db_invoice.invoice_no = invoice.invoice_no
    db_invoice.invoice_date = invoice.invoice_date
    db_invoice.customer_id = invoice.customer_id
    db_invoice.total_amount = invoice.total_amount
    db_invoice.tax_amount = invoice.tax_amount
    db_invoice.remark = invoice.remark

    db.commit()
    db.refresh(db_invoice)

    return get_invoice(db_invoice.id, db, current_user)


@router.delete("/{invoice_id}")
def delete_invoice(invoice_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 软删除：标记为已作废
    db_invoice.status = "已作废"
    db.commit()

    return {"message": "发票已作废"}


@router.get("/orders/{order_id}/invoice-info", response_model=OrderInvoiceInfo)
def get_order_invoice_info(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取订单的开票信息"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 计算已开票金额
    invoiced_amount = db.query(func.sum(InvoiceItem.amount)).filter(
        InvoiceItem.order_id == order_id
    ).scalar() or 0

    # 计算可开票余额
    balance_amount = order.total_amount - invoiced_amount

    return {
        "order_id": order.id,
        "order_no": order.id,
        "order_date": order.order_date,
        "total_amount": order.total_amount,
        "invoiced_amount": invoiced_amount,
        "balance_amount": balance_amount
    }


@router.get("/orders/available", response_model=List[dict])
def get_available_orders_for_invoice(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取客户可开票的订单列表"""
    # 获取该客户所有订单
    orders = db.query(SalesOrder).filter(SalesOrder.customer_id == customer_id).all()

    result = []
    for order in orders:
        # 计算已开票金额
        invoiced_amount = db.query(func.sum(InvoiceItem.amount)).filter(
            InvoiceItem.order_id == order.id
        ).scalar() or 0

        # 可开票余额
        balance_amount = order.total_amount - invoiced_amount

        # 只返回还有可开票余额的订单
        if balance_amount > 0:
            result.append({
                "order_id": order.id,
                "order_no": order.id,
                "order_date": order.order_date,
                "total_amount": order.total_amount,
                "invoiced_amount": invoiced_amount,
                "balance_amount": balance_amount
            })

    return result