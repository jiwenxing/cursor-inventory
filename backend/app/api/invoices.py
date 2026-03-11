from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Invoice, InvoiceItem, SalesOrder, SalesOrderItem, Customer, User, SalesOrderItemInvoice
from app.schemas import InvoiceCreate, InvoiceResponse, PaginatedInvoicesResponse, OrderInvoiceInfo, OrderInvoiceSummary, SalesOrderItemForInvoice, InvoiceCreateFromOrder
from app.utils import get_current_user

router = APIRouter()


@router.get("/next-no")
def get_next_invoice_no(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """生成下一个发票号"""
    today = datetime.now().strftime("%Y%m%d")
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

    return {"invoice_no": f"{today_prefix}{new_seq:04d}"}


@router.get("/", response_model=PaginatedInvoicesResponse)
def get_invoices(
    skip: int = 0,
    limit: int = 15,
    customer_id: Optional[int] = None,
    invoice_no: Optional[str] = None,
    order_no: Optional[str] = None,
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

    # 按订单号筛选（关联的发票明细）
    if order_no:
        query = query.join(InvoiceItem).filter(InvoiceItem.order_no == order_no)

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

    # 查询每个订单的详细信息
    items_data = []
    for item in invoice.items:
        order = db.query(SalesOrder).filter(SalesOrder.id == item.order_id).first()

        # 查询该发票明细对应的商品明细开票记录
        order_item_invoices = db.query(SalesOrderItemInvoice).filter(
            SalesOrderItemInvoice.invoice_item_id == item.id
        ).all()

        # 构建商品明细数据
        product_items = []
        for oii in order_item_invoices:
            order_item = oii.order_item
            product = order_item.product if order_item else None
            product_items.append({
                "id": oii.id,
                "order_item_id": oii.order_item_id,
                "product_id": order_item.product_id if order_item else None,
                "product_name": product.name if product else None,
                "product_model": product.model if product else None,
                "quantity": oii.invoiced_quantity,
                "unit_price": order_item.discounted_price_tax if order_item else 0,
                "amount": oii.invoiced_amount,
                "tax_amount": oii.invoiced_tax_amount
            })

        items_data.append({
            "id": item.id,
            "invoice_id": item.invoice_id,
            "order_id": item.order_id,
            "order_no": item.order_no,
            "order_date": order.order_date if order else None,
            "customer_name": order.customer.name if order and order.customer else None,
            "order_total_amount": order.total_amount if order else 0,
            "contract_amount": order.contract_amount if order else 0,
            "amount": item.amount,
            "tax_amount": item.tax_amount,
            "product_items": product_items  # 商品明细
        })

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
        "items": items_data
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

    # 创建发票明细和商品明细开票记录
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
        db.flush()

        # 为该订单的所有商品明细创建开票记录（按金额比例分配）
        order_items = db.query(SalesOrderItem).filter(SalesOrderItem.order_id == item.order_id).all()
        order_total = sum(oi.line_total for oi in order_items)

        if order_total > 0:
            for order_item in order_items:
                # 按该商品明细占订单总金额的比例分配开票金额
                ratio = order_item.line_total / order_total
                invoiced_amount = item.amount * ratio
                invoiced_tax = item.tax_amount * ratio
                # 计算开票数量（按金额比例）
                invoiced_quantity = order_item.quantity * ratio

                db_soi = SalesOrderItemInvoice(
                    order_item_id=order_item.id,
                    invoice_item_id=db_item.id,
                    invoiced_quantity=invoiced_quantity,
                    invoiced_amount=invoiced_amount,
                    invoiced_tax_amount=invoiced_tax
                )
                db.add(db_soi)

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


@router.get("/orders/{order_id}/items-for-invoice", response_model=OrderInvoiceSummary)
def get_order_items_for_invoice(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取订单商品明细（用于开票），包含已开票信息"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 获取订单的所有商品明细
    items = db.query(SalesOrderItem).filter(SalesOrderItem.order_id == order_id).all()

    # 计算每个商品明细的已开票数量和金额
    items_data = []
    total_invoiced = 0
    for item in items:
        # 查询该商品明细已开票数量和金额
        invoiced_info = db.query(
            func.sum(SalesOrderItemInvoice.invoiced_quantity).label("quantity"),
            func.sum(SalesOrderItemInvoice.invoiced_amount).label("amount")
        ).filter(
            SalesOrderItemInvoice.order_item_id == item.id
        ).first()

        invoiced_quantity = invoiced_info.quantity or 0
        invoiced_amount = invoiced_info.amount or 0
        available_quantity = item.quantity - invoiced_quantity
        available_amount = item.line_total - invoiced_amount

        total_invoiced += invoiced_amount

        items_data.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": item.product.name if item.product else None,
            "product_model": item.product.model if item.product else None,
            "quantity": item.quantity,
            "invoiced_quantity": invoiced_quantity,
            "available_quantity": available_quantity,
            "discounted_price_tax": item.discounted_price_tax,  # 含税优惠价
            "line_total": item.line_total,
            "available_amount": available_amount
        })

    # 计算订单总的可开票余额
    balance_amount = order.total_amount - total_invoiced

    return {
        "order_id": order.id,
        "order_no": order.id,
        "order_date": order.order_date,
        "customer_id": order.customer_id,
        "customer_name": order.customer.name if order.customer else None,
        "total_amount": order.total_amount,
        "invoiced_amount": total_invoiced,
        "balance_amount": balance_amount,
        "items": items_data
    }


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


@router.post("/from-order", response_model=InvoiceResponse)
def create_invoice_from_order(
    invoice_data: InvoiceCreateFromOrder,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从订单创建发票（支持按商品明细开票）"""
    # 验证客户存在
    customer = db.query(Customer).filter(Customer.id == invoice_data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 检查发票号是否已存在
    existing = db.query(Invoice).filter(Invoice.invoice_no == invoice_data.invoice_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="发票号已存在")

    # 验证并计算金额
    total_amount = 0
    total_tax = 0

    # 按订单分组
    order_ids = set(item.order_item_id for item in invoice_data.items)
    order_item_map = {item.order_item_id: item for item in invoice_data.items}

    # 验证每个订单商品明细
    for order_item_id in order_ids:
        order_item = db.query(SalesOrderItem).filter(SalesOrderItem.id == order_item_id).first()
        if not order_item:
            raise HTTPException(status_code=404, detail=f"订单商品明细ID {order_item_id} 不存在")

        # 验证订单属于该客户
        if order_item.order.customer_id != invoice_data.customer_id:
            raise HTTPException(status_code=400, detail=f"订单商品明细 {order_item_id} 不属于该客户")

        item_data = order_item_map[order_item_id]

        # 检查可开票数量
        invoiced_info = db.query(
            func.sum(SalesOrderItemInvoice.invoiced_quantity).label("quantity")
        ).filter(
            SalesOrderItemInvoice.order_item_id == order_item_id
        ).first()
        invoiced_quantity = invoiced_info.quantity or 0
        available_quantity = order_item.quantity - invoiced_quantity

        if item_data.quantity > available_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"商品 {order_item.product.name if order_item.product else order_item_id} 开票数量超过可开票数量（{available_quantity}）"
            )

        total_amount += item_data.amount
        total_tax += item_data.tax_amount

    # 创建发票
    db_invoice = Invoice(
        invoice_no=invoice_data.invoice_no,
        invoice_date=invoice_data.invoice_date,
        customer_id=invoice_data.customer_id,
        total_amount=total_amount,
        tax_amount=total_tax,
        remark=invoice_data.remark,
        created_by=current_user.id
    )
    db.add(db_invoice)
    db.flush()

    # 创建发票明细和商品明细开票记录
    order_items_processed = {}  # 用于合并同一订单的开票明细

    for item_data in invoice_data.items:
        order_item_id = item_data.order_item_id
        order_item = db.query(SalesOrderItem).filter(SalesOrderItem.id == order_item_id).first()

        # 查找或创建该订单的发票明细
        if order_item.order_id not in order_items_processed:
            db_item = InvoiceItem(
                invoice_id=db_invoice.id,
                order_id=order_item.order_id,
                order_item_id=order_item_id,
                order_no=order_item.order_id,
                amount=0,  # 先设为0，后面累加
                tax_amount=0
            )
            db.add(db_item)
            db.flush()
            order_items_processed[order_item.order_id] = {
                "item": db_item,
                "amount": 0,
                "tax_amount": 0
            }

        # 累加金额
        order_items_processed[order_item.order_id]["amount"] += item_data.amount
        order_items_processed[order_item.order_id]["tax_amount"] += item_data.tax_amount

        # 获取发票明细ID
        invoice_item_id = order_items_processed[order_item.order_id]["item"].id

        # 创建商品明细开票记录
        db_soi = SalesOrderItemInvoice(
            order_item_id=order_item_id,
            invoice_item_id=invoice_item_id,  # 直接设置正确的ID
            invoiced_quantity=item_data.quantity,
            invoiced_amount=item_data.amount,
            invoiced_tax_amount=item_data.tax_amount
        )
        db.add(db_soi)

    db.flush()

    # 更新发票明细的实际金额
    for order_id, data in order_items_processed.items():
        data["item"].amount = data["amount"]
        data["item"].tax_amount = data["tax_amount"]

    db.commit()
    db.refresh(db_invoice)

    return get_invoice(db_invoice.id, db, current_user)