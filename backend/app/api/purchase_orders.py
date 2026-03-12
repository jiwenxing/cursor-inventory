from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import PurchaseOrder, PurchaseOrderItem, Product, Supplier, User, InventorySummary, PurchaseInvoiceItem, SalesOrder, PurchaseItemStatus
from app.schemas import PurchaseOrderCreate, PurchaseOrderResponse, PaginatedPurchaseOrdersResponse, PurchaseOrderInvoiceInfo, PurchaseOrderCreateFromSalesOrder, PurchaseStatusUpdate, PurchaseOrderReceive, PurchaseOrderBatchCreate, PurchaseOrderGroupCreate
from app.utils import get_current_user

router = APIRouter()


def order_to_dict(order: PurchaseOrder, db: Session = None) -> dict:
    """将采购订单对象转换为字典"""
    # 计算已开票金额（预留：第 4 步进项发票）
    invoiced_amount = 0
    if db:
        invoiced_amount = db.query(func.sum(PurchaseInvoiceItem.amount)).filter(
            PurchaseInvoiceItem.order_id == order.id
        ).scalar() or 0

    balance_amount = order.total_amount - invoiced_amount

    # 获取来源销售订单 ID（订单级别）
    source_sales_order_id = order.source_sales_order_id

    return {
        "id": order.id,
        "order_date": order.order_date,
        "supplier_id": order.supplier_id,
        "supplier_name": order.supplier.name if order.supplier else None,
        "purchaser_id": order.purchaser_id,
        "purchaser_name": order.purchaser.name if order.purchaser else None,
        "total_amount": order.total_amount,
        "status": order.status,
        "purchase_status": order.purchase_status,  # 订单级别的采购状态
        "source_sales_order_id": source_sales_order_id,  # 订单级别的来源销售订单 ID
        "remark": order.remark,
        "created_at": order.created_at,
        "invoiced_amount": invoiced_amount,
        "balance_amount": balance_amount,
        "items": [{
            "id": item.id,
            "product_id": item.product_id,
            "product_name": item.product.name if item.product else None,
            "product_model": item.product.model if item.product else None,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "received_quantity": item.received_quantity,
            "unreceived_quantity": item.quantity - item.received_quantity,
            "line_total": item.line_total,
            "current_stock": db.query(InventorySummary.current_stock).filter(
                InventorySummary.product_id == item.product_id
            ).scalar() or 0
        } for item in order.items]
    }


def calculate_order_amounts(items_data):
    """计算采购订单金额"""
    total = 0
    calculated_items = []
    for item in items_data:
        line_total = item["quantity"] * item["unit_price"]
        total += line_total
        calculated_items.append({
            **item,
            "line_total": line_total,
            "received_quantity": 0,
            "source_sales_order_id": item.get("source_sales_order_id")
        })
    return calculated_items, total


@router.get("/", response_model=PaginatedPurchaseOrdersResponse)
def get_purchase_orders(
    skip: int = 0,
    limit: int = 15,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(PurchaseOrder)

    # 按供应商 ID 筛选
    if supplier_id is not None:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)

    # 按状态筛选
    if status:
        query = query.filter(PurchaseOrder.status == status)

    # 按日期范围筛选
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(PurchaseOrder.order_date >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(PurchaseOrder.order_date <= end)
        except ValueError:
            pass

    # 按金额范围筛选
    if min_amount is not None:
        query = query.filter(PurchaseOrder.total_amount >= min_amount)
    if max_amount is not None:
        query = query.filter(PurchaseOrder.total_amount <= max_amount)

    # 获取总数
    total = query.count()

    # 分页查询
    orders = query.order_by(PurchaseOrder.order_date.desc()).offset(skip).limit(limit).all()

    result = [order_to_dict(order, db) for order in orders]

    return {"items": result, "total": total}


@router.get("/{order_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    return order_to_dict(order, db)


@router.post("/", response_model=PurchaseOrderResponse)
def create_purchase_order(order: PurchaseOrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 验证供应商存在
    supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")

    # 计算金额
    items_data = [item.dict() for item in order.items]
    calculated_items, total_amount = calculate_order_amounts(items_data)

    # 验证商品是否存在
    for item_data in calculated_items:
        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"商品 ID {item_data['product_id']} 不存在")

    # 创建订单
    db_order = PurchaseOrder(
        order_date=order.order_date,
        supplier_id=order.supplier_id,
        purchaser_id=current_user.id,
        total_amount=total_amount,
        source_sales_order_id=order.source_sales_order_id,
        remark=order.remark
    )
    db.add(db_order)
    db.flush()

    # 创建订单明细
    for item_data in calculated_items:
        db_item = PurchaseOrderItem(
            order_id=db_order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            received_quantity=item_data["received_quantity"],
            line_total=item_data["line_total"]
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_order)
    return get_purchase_order(db_order.id, db, current_user)


@router.post("/from-sales-order/{sales_order_id}", response_model=PurchaseOrderResponse)
def create_purchase_order_from_sales_order(
    sales_order_id: int,
    order_data: PurchaseOrderCreateFromSalesOrder,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从销售订单创建采购订单"""
    # 验证销售订单存在
    sales_order = db.query(SalesOrder).filter(SalesOrder.id == sales_order_id).first()
    if not sales_order:
        raise HTTPException(status_code=404, detail="销售订单不存在")

    # 验证供应商存在
    supplier = db.query(Supplier).filter(Supplier.id == order_data.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")

    # 计算金额
    items_data = [item.dict() for item in order_data.items]
    calculated_items, total_amount = calculate_order_amounts(items_data)

    # 验证商品是否存在
    for item_data in calculated_items:
        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"商品 ID {item_data['product_id']} 不存在")

    # 创建采购订单
    db_order = PurchaseOrder(
        order_date=order_data.order_date,
        supplier_id=order_data.supplier_id,
        purchaser_id=current_user.id,
        total_amount=total_amount,
        source_sales_order_id=sales_order_id,
        remark=order_data.remark or f"从销售订单 SO-{sales_order_id} 生成"
    )
    db.add(db_order)
    db.flush()

    # 创建订单明细
    for item_data in calculated_items:
        db_item = PurchaseOrderItem(
            order_id=db_order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            received_quantity=item_data["received_quantity"],
            line_total=item_data["line_total"]
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_order)
    return get_purchase_order(db_order.id, db, current_user)


@router.put("/{order_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(order_id: int, order: PurchaseOrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="采购订单不存在")

    # 已完成的订单不能修改
    if db_order.status == "已完成":
        raise HTTPException(status_code=400, detail="已完成的订单不能修改")

    # 验证供应商存在
    supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")

    # 删除旧明细
    db.query(PurchaseOrderItem).filter(PurchaseOrderItem.order_id == order_id).delete()

    # 更新订单基本信息
    db_order.order_date = order.order_date
    db_order.supplier_id = order.supplier_id
    db_order.source_sales_order_id = order.source_sales_order_id
    db_order.remark = order.remark

    # 重新计算金额并创建明细
    items_data = [item.dict() for item in order.items]
    calculated_items, total_amount = calculate_order_amounts(items_data)
    db_order.total_amount = total_amount

    db.flush()

    # 创建新明细
    for item_data in calculated_items:
        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"商品 ID {item_data['product_id']} 不存在")

        db_item = PurchaseOrderItem(
            order_id=db_order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            received_quantity=0,
            line_total=item_data["line_total"]
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_order)
    return get_purchase_order(db_order.id, db, current_user)


@router.delete("/{order_id}")
def delete_purchase_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="采购订单不存在")

    # 已有入库记录的订单不能删除
    has_received = any(item.received_quantity > 0 for item in db_order.items)
    if has_received:
        raise HTTPException(status_code=400, detail="已有入库记录的订单不能删除")

    # 已有商品下单给供应商，不能删除
    if db_order.purchase_status == "已下单":
        raise HTTPException(status_code=400, detail="已下单给供应商，无法删除订单")

    db.delete(db_order)
    db.commit()
    return {"message": "删除成功"}


@router.get("/orders/{order_id}/invoice-info", response_model=PurchaseOrderInvoiceInfo)
def get_purchase_order_invoice_info(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取采购订单的开票信息（预留：第 4 步进项发票）"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")

    # 计算已开票金额
    invoiced_amount = db.query(func.sum(PurchaseInvoiceItem.amount)).filter(
        PurchaseInvoiceItem.order_id == order_id
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
def get_available_orders_for_purchase_invoice(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取供应商可开票的采购订单列表（预留：第 4 步进项发票）"""
    # 获取该供应商所有订单
    orders = db.query(PurchaseOrder).filter(PurchaseOrder.supplier_id == supplier_id).all()

    result = []
    for order in orders:
        # 计算已开票金额
        invoiced_amount = db.query(func.sum(PurchaseInvoiceItem.amount)).filter(
            PurchaseInvoiceItem.order_id == order.id
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


@router.put("/{order_id}/purchase-status")
def update_purchase_order_status(
    order_id: int,
    status_data: PurchaseStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修改采购订单的采购状态"""
    # 验证采购订单存在
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")

    # 已有入库记录的订单不能修改采购状态
    has_received = any(item.received_quantity > 0 for item in order.items)
    if has_received:
        raise HTTPException(status_code=400, detail="已有入库记录的订单不能修改采购状态")

    # 验证状态值
    valid_statuses = ["待下单", "待确认", "已下单"]
    if status_data.purchase_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效的状态值，有效值为：{', '.join(valid_statuses)}")

    # 更新状态
    order.purchase_status = status_data.purchase_status

    db.commit()
    return {"message": "状态更新成功", "purchase_status": order.purchase_status}


@router.post("/{order_id}/receive")
def receive_purchase_order(
    order_id: int,
    receive_data: PurchaseOrderReceive,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """采购入库（带约束检查）"""
    # 验证采购订单存在
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")

    # 检查订单状态
    if order.status == "已完成":
        raise HTTPException(status_code=400, detail="已完成的订单无法入库")

    # 检查采购状态：必须为「已下单」
    if order.purchase_status != "已下单":
        raise HTTPException(
            status_code=400,
            detail=f"采购订单状态为「{order.purchase_status}」，尚未下单给供应商，无法入库"
        )

    for receive_item in receive_data.items:
        order_item_id = receive_item.get("order_item_id")
        received_quantity = receive_item.get("received_quantity", 0)

        if not order_item_id:
            raise HTTPException(status_code=400, detail="缺少 order_item_id")

        # 验证明细存在
        item = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.id == order_item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"采购明细 {order_item_id} 不存在")

        # 检查数量
        unreceived_quantity = item.quantity - item.received_quantity
        if received_quantity > unreceived_quantity:
            raise HTTPException(status_code=400, detail=f"入库数量不能超过未入库数量（当前未入库：{unreceived_quantity}）")

        if received_quantity <= 0:
            continue

        # 更新已入库数量
        item.received_quantity += received_quantity

        # 生成入库记录
        inventory_record = InventoryRecord(
            product_id=item.product_id,
            type="IN",
            quantity=received_quantity,
            related_order_id=order_id,
            related_order_type="purchase"
        )
        db.add(inventory_record)

        # 更新库存汇总
        summary = db.query(InventorySummary).filter(InventorySummary.product_id == item.product_id).first()
        if summary:
            summary.current_stock += received_quantity
        else:
            summary = InventorySummary(product_id=item.product_id, current_stock=received_quantity)
            db.add(summary)

    # 更新订单状态
    total_received = sum(i.received_quantity for i in order.items)
    total_quantity = sum(i.quantity for i in order.items)
    if total_received >= total_quantity:
        order.status = "已完成"
    elif total_received > 0:
        order.status = "部分入库"

    db.commit()
    return {"message": "入库成功", "order_status": order.status}


@router.post("/batch-from-sales-order/{sales_order_id}")
def create_purchase_orders_batch(
    sales_order_id: int,
    batch_data: PurchaseOrderBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从销售订单批量创建采购订单（按供应商分组）"""
    # 验证销售订单
    sales_order = db.query(SalesOrder).filter(SalesOrder.id == sales_order_id).first()
    if not sales_order:
        raise HTTPException(404, "销售订单不存在")

    if not batch_data.groups:
        raise HTTPException(400, "至少需要一个供应商分组")

    created_orders = []

    for group in batch_data.groups:
        if not group.items:
            continue  # 跳过空分组

        # 验证供应商
        supplier = db.query(Supplier).filter(Supplier.id == group.supplier_id).first()
        if not supplier:
            raise HTTPException(404, f"供应商 {group.supplier_id} 不存在")

        # 计算总金额
        total_amount = sum(item.quantity * item.unit_price for item in group.items)

        # 创建采购订单
        db_order = PurchaseOrder(
            order_date=group.order_date or batch_data.order_date,
            supplier_id=group.supplier_id,
            purchaser_id=current_user.id,
            total_amount=total_amount,
            source_sales_order_id=sales_order_id,
            remark=group.remark or batch_data.remark or f"从销售订单 SO-{sales_order_id} 生成"
        )
        db.add(db_order)
        db.flush()

        # 创建订单明细
        for item in group.items:
            db_item = PurchaseOrderItem(
                order_id=db_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                received_quantity=0,
                line_total=item.quantity * item.unit_price
            )
            db.add(db_item)

        created_orders.append({
            "order_id": db_order.id,
            "supplier_id": group.supplier_id,
            "supplier_name": group.supplier_name,
            "total_amount": total_amount
        })

    db.commit()

    return {
        "message": f"成功创建 {len(created_orders)} 个采购订单",
        "orders": created_orders
    }
