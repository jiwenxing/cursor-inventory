from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.database import get_db
from app.models import InventoryRecord, InventorySummary, Product, User, PurchaseOrder, PurchaseOrderItem
from app.schemas import InventoryRecordCreate, InventoryRecordResponse, InventorySummaryResponse
from app.utils import get_current_user
from app.timezone import to_cst_datetime

router = APIRouter()


@router.get("/summary", response_model=List[InventorySummaryResponse])
def get_inventory_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    summaries = db.query(InventorySummary).join(Product).all()
    result = []
    for summary in summaries:
        result.append({
            "product_id": summary.product_id,
            "product_name": summary.product.name,
            "product_model": summary.product.model,
            "product_brand": summary.product.brand,
            "supplier_id": summary.product.supplier_id,
            "supplier_name": summary.product.supplier.name if summary.product.supplier else None,
            "current_stock": summary.current_stock
        })
    return result


@router.get("/records", response_model=List[InventoryRecordResponse])
def get_inventory_records(
    skip: int = 0,
    limit: int = 100,
    purchase_order_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(InventoryRecord)

    # 按采购订单筛选
    if purchase_order_id is not None:
        query = query.filter(
            InventoryRecord.related_order_id == purchase_order_id,
            InventoryRecord.related_order_type == "purchase"
        )

    records = query.order_by(InventoryRecord.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for record in records:
        result.append({
            "id": record.id,
            "product_id": record.product_id,
            "product_name": record.product.name if record.product else None,
            "product_model": record.product.model if record.product else None,
            "product_brand": record.product.brand if record.product else None,
            "supplier_id": record.product.supplier_id if record.product else None,
            "supplier_name": record.product.supplier.name if record.product and record.product.supplier else None,
            "type": record.type,
            "quantity": record.quantity,
            "related_order_id": record.related_order_id,
            "related_order_type": record.related_order_type,
            "created_at": to_cst_datetime(record.created_at)
        })
    return result


@router.post("/in", response_model=InventoryRecordResponse)
def create_inventory_in(
    record: InventoryRecordCreate,
    purchase_order_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if record.type != "IN":
        raise HTTPException(status_code=400, detail="类型必须为 IN")

    product = db.query(Product).filter(Product.id == record.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    # 如果关联了采购订单，验证并更新订单状态
    if purchase_order_id is not None:
        purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == purchase_order_id).first()
        if not purchase_order:
            raise HTTPException(status_code=404, detail="采购订单不存在")

        # 查找对应的订单明细
        order_item = db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.order_id == purchase_order_id,
            PurchaseOrderItem.product_id == record.product_id
        ).first()

        if not order_item:
            raise HTTPException(status_code=400, detail="该商品不在采购订单中")

        # 检查入库数量是否超过订单数量
        new_received = order_item.received_quantity + record.quantity
        if new_received > order_item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"入库数量超过订单数量（订单：{order_item.quantity}, 已入库：{order_item.received_quantity}, 本次：{record.quantity}）"
            )

        # 更新订单明细的已入库数量
        order_item.received_quantity = new_received

        # 更新采购订单状态
        total_quantity = sum(item.quantity for item in purchase_order.items)
        total_received = sum(item.received_quantity for item in purchase_order.items)

        if total_received >= total_quantity:
            purchase_order.status = "已完成"
        elif total_received > 0:
            purchase_order.status = "部分入库"
        else:
            purchase_order.status = "待入库"

    # 创建库存流水
    db_record = InventoryRecord(
        product_id=record.product_id,
        type="IN",
        quantity=record.quantity,
        related_order_id=purchase_order_id,
        related_order_type="purchase" if purchase_order_id else None
    )
    db.add(db_record)

    # 更新库存汇总
    summary = db.query(InventorySummary).filter(InventorySummary.product_id == record.product_id).first()
    if summary:
        summary.current_stock += record.quantity
    else:
        summary = InventorySummary(product_id=record.product_id, current_stock=record.quantity)
        db.add(summary)

    db.commit()
    db.refresh(db_record)

    return {
        "id": db_record.id,
        "product_id": db_record.product_id,
        "product_name": product.name,
        "product_model": product.model,
        "product_brand": product.brand,
        "supplier_id": product.supplier_id,
        "supplier_name": product.supplier.name if product.supplier else None,
        "type": db_record.type,
        "quantity": db_record.quantity,
        "related_order_id": db_record.related_order_id,
        "related_order_type": db_record.related_order_type,
        "created_at": to_cst_datetime(db_record.created_at)
    }


@router.get("/purchase-orders/pending", response_model=List[dict])
def get_pending_purchase_orders_for_receive(
    supplier_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取待入库的采购订单列表（用于入库时选择）"""
    query = db.query(PurchaseOrder).filter(
        PurchaseOrder.status.in_(["待入库", "部分入库"])
    )

    if supplier_id is not None:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)

    orders = query.order_by(PurchaseOrder.order_date.desc()).all()

    result = []
    for order in orders:
        items = []
        for item in order.items:
            unreceived = item.quantity - item.received_quantity
            if unreceived > 0:
                items.append({
                    "order_item_id": item.id,
                    "product_id": item.product_id,
                    "product_name": item.product.name if item.product else None,
                    "product_model": item.product.model if item.product else None,
                    "quantity": item.quantity,
                    "received_quantity": item.received_quantity,
                    "unreceived_quantity": unreceived,
                    "unit_price": item.unit_price
                })

        if items:  # 只返回有待入库商品的订单
            result.append({
                "order_id": order.id,
                "order_date": to_cst_datetime(order.order_date),
                "supplier_id": order.supplier_id,
                "supplier_name": order.supplier.name if order.supplier else None,
                "status": order.status,
                "items": items
            })

    return result
