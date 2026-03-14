from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import SalesOrder, SalesOrderItem, Product, Customer, User, InventoryRecord, InventorySummary, InvoiceItem, PaymentRecord, Supplier
from app.schemas import SalesOrderCreate, SalesOrderResponse, SalesOrderItemResponse, PurchaseSuggestionResponse, PurchaseSuggestionItem, PurchaseSuggestionGroup
from app.utils import get_current_user
from app.timezone import to_cst_datetime

router = APIRouter()


class PaginatedOrdersResponse(BaseModel):
    items: List[dict]
    total: int


def order_to_dict(order: SalesOrder, db: Session = None) -> dict:
    """将订单对象转换为字典"""
    # 计算已开票金额
    invoiced_amount = 0
    if db:
        invoiced_amount = db.query(func.sum(InvoiceItem.amount)).filter(
            InvoiceItem.order_id == order.id
        ).scalar() or 0

    balance_amount = order.total_amount - invoiced_amount

    # 计算已付金额和未付金额
    paid_amount = order.paid_amount if order.paid_amount else 0
    unpaid_amount = order.total_amount - paid_amount

    return {
        "id": order.id,
        "order_date": to_cst_datetime(order.order_date),
        "customer_id": order.customer_id,
        "customer_name": order.customer.name if order.customer else None,
        "salesperson_id": order.salesperson_id,
        "salesperson_name": order.salesperson.name if order.salesperson else None,
        "contract_no": order.contract_no,
        "contract_date": to_cst_datetime(order.contract_date),
        "contract_amount": order.contract_amount,
        "payment_status": order.payment_status,
        "total_amount": order.total_amount,
        "paid_amount": paid_amount,
        "unpaid_amount": unpaid_amount,
        "invoiced_amount": invoiced_amount,
        "balance_amount": balance_amount,
        "created_at": to_cst_datetime(order.created_at),
        "items": [{
            "id": item.id,
            "product_id": item.product_id,
            "customer_product_code": item.customer_product_code,
            "product_name": item.product.name if item.product else None,
            "product_model": item.product.model if item.product else None,
            "quantity": item.quantity,
            "unit_price_tax": item.unit_price_tax,
            "discounted_price_tax": item.discounted_price_tax,
            "discount_rate": item.discount_rate,
            "final_unit_price_tax": item.final_unit_price_tax,
            "line_total": item.line_total,
            "shipped_quantity": item.shipped_quantity,
            "unshipped_quantity": item.unshipped_quantity
        } for item in order.items]
    }


def calculate_order_amounts(items_data):
    """计算订单金额"""
    total = 0
    calculated_items = []
    for item in items_data:
        # 含税优惠价作为最终单价
        final_price = item.get("discounted_price_tax", item["unit_price_tax"])
        line_total = item["quantity"] * final_price
        total += line_total

        # 计算折扣率：1 - (含税优惠价 / 含税单价)
        unit_price = item["unit_price_tax"]
        if unit_price and unit_price != 0:
            discount_rate = 1 - (final_price / unit_price)
        else:
            discount_rate = 0

        calculated_items.append({
            **item,
            "final_unit_price_tax": final_price,
            "line_total": line_total,
            "discount_rate": discount_rate,
            "unshipped_quantity": item["quantity"]
        })
    return calculated_items, total


@router.get("/", response_model=PaginatedOrdersResponse)
def get_sales_orders(
    skip: int = 0,
    limit: int = 15,
    customer_id: Optional[int] = None,
    payment_status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(SalesOrder)

    # 按客户 ID 筛选
    if customer_id is not None:
        query = query.filter(SalesOrder.customer_id == customer_id)

    # 按付款状态筛选
    if payment_status:
        query = query.filter(SalesOrder.payment_status == payment_status)

    # 按日期范围筛选
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(SalesOrder.order_date >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(SalesOrder.order_date <= end)
        except ValueError:
            pass

    # 按金额范围筛选
    if min_amount is not None:
        query = query.filter(SalesOrder.total_amount >= min_amount)
    if max_amount is not None:
        query = query.filter(SalesOrder.total_amount <= max_amount)

    # 获取总数
    total = query.count()

    # 分页查询
    orders = query.order_by(SalesOrder.order_date.desc()).offset(skip).limit(limit).all()

    result = [order_to_dict(order, db) for order in orders]

    return {"items": result, "total": total}


@router.get("/{order_id}", response_model=SalesOrderResponse)
def get_sales_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order_to_dict(order, db)


@router.post("/", response_model=SalesOrderResponse)
def create_sales_order(order: SalesOrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 验证客户存在
    customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 计算金额
    items_data = [item.dict() for item in order.items]
    calculated_items, total_amount = calculate_order_amounts(items_data)

    # 创建订单
    db_order = SalesOrder(
        order_date=order.order_date,
        customer_id=order.customer_id,
        salesperson_id=current_user.id,
        contract_no=order.contract_no,
        contract_date=order.contract_date,
        contract_amount=order.contract_amount,
        payment_status=order.payment_status,
        total_amount=total_amount
    )
    db.add(db_order)
    db.flush()

    # 创建订单明细并生成库存流水
    for item_data in calculated_items:
        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"商品 ID {item_data['product_id']} 不存在")

        db_item = SalesOrderItem(
            order_id=db_order.id,
            product_id=item_data["product_id"],
            customer_product_code=item_data.get("customer_product_code"),
            quantity=item_data["quantity"],
            unit_price_tax=item_data["unit_price_tax"],
            discounted_price_tax=item_data["discounted_price_tax"],
            discount_rate=item_data.get("discount_rate", 0),
            final_unit_price_tax=item_data["final_unit_price_tax"],
            line_total=item_data["line_total"],
            shipped_quantity=0,
            unshipped_quantity=item_data["unshipped_quantity"]
        )
        db.add(db_item)

        # 生成库存 OUT 流水
        inventory_record = InventoryRecord(
            product_id=item_data["product_id"],
            type="OUT",
            quantity=item_data["quantity"],
            related_order_id=db_order.id
        )
        db.add(inventory_record)

        # 更新库存汇总
        summary = db.query(InventorySummary).filter(InventorySummary.product_id == item_data["product_id"]).first()
        if summary:
            summary.current_stock -= item_data["quantity"]
        else:
            summary = InventorySummary(product_id=item_data["product_id"], current_stock=-item_data["quantity"])
            db.add(summary)

    db.commit()
    db.refresh(db_order)
    return get_sales_order(db_order.id, db, current_user)


@router.put("/{order_id}", response_model=SalesOrderResponse)
def update_sales_order(order_id: int, order: SalesOrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 回滚之前的库存流水
    for item in db_order.items:
        # 回滚库存
        summary = db.query(InventorySummary).filter(InventorySummary.product_id == item.product_id).first()
        if summary:
            summary.current_stock += item.quantity
        # 删除库存流水
        db.query(InventoryRecord).filter(
            InventoryRecord.related_order_id == order_id,
            InventoryRecord.product_id == item.product_id,
            InventoryRecord.type == "OUT"
        ).delete()

    # 删除旧明细
    db.query(SalesOrderItem).filter(SalesOrderItem.order_id == order_id).delete()

    # 更新订单基本信息
    db_order.order_date = order.order_date
    db_order.customer_id = order.customer_id
    db_order.contract_no = order.contract_no
    db_order.contract_date = order.contract_date
    db_order.contract_amount = order.contract_amount
    db_order.payment_status = order.payment_status

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

        db_item = SalesOrderItem(
            order_id=db_order.id,
            product_id=item_data["product_id"],
            customer_product_code=item_data.get("customer_product_code"),
            quantity=item_data["quantity"],
            unit_price_tax=item_data["unit_price_tax"],
            discounted_price_tax=item_data["discounted_price_tax"],
            discount_rate=item_data.get("discount_rate", 0),
            final_unit_price_tax=item_data["final_unit_price_tax"],
            line_total=item_data["line_total"],
            shipped_quantity=0,
            unshipped_quantity=item_data["unshipped_quantity"]
        )
        db.add(db_item)

        # 生成库存 OUT 流水
        inventory_record = InventoryRecord(
            product_id=item_data["product_id"],
            type="OUT",
            quantity=item_data["quantity"],
            related_order_id=db_order.id
        )
        db.add(inventory_record)

        # 更新库存汇总
        summary = db.query(InventorySummary).filter(InventorySummary.product_id == item_data["product_id"]).first()
        if summary:
            summary.current_stock -= item_data["quantity"]
        else:
            summary = InventorySummary(product_id=item_data["product_id"], current_stock=-item_data["quantity"])
            db.add(summary)

    db.commit()
    db.refresh(db_order)
    return get_sales_order(db_order.id, db, current_user)


@router.delete("/{order_id}")
def delete_sales_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 回滚库存
    for item in db_order.items:
        summary = db.query(InventorySummary).filter(InventorySummary.product_id == item.product_id).first()
        if summary:
            summary.current_stock += item.quantity

    # 删除库存流水
    db.query(InventoryRecord).filter(InventoryRecord.related_order_id == order_id).delete()

    # 删除关联的发票项目
    db.query(InvoiceItem).filter(InvoiceItem.order_id == order_id).delete()

    # 删除订单（级联删除明细）
    db.delete(db_order)
    db.commit()
    return {"message": "删除成功"}


@router.get("/{order_id}/purchase-suggestions", response_model=PurchaseSuggestionResponse)
def get_purchase_suggestions(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取销售订单的采购建议（按供应商自动分组）"""
    from collections import defaultdict

    # 获取销售订单
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="销售订单不存在")

    # 获取订单明细
    order_items = db.query(SalesOrderItem).filter(SalesOrderItem.order_id == order_id).all()
    if not order_items:
        return PurchaseSuggestionResponse(
            sales_order_id=order_id,
            sales_order_no=order_id,
            order_date=order.order_date,
            customer_name=order.customer.name if order.customer else None,
            groups=[],
            total_amount=0
        )

    # 按供应商分组
    groups_dict = defaultdict(list)
    for item in order_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product or not product.supplier_id:
            continue  # 跳过无供应商的商品

        # 获取当前库存
        inventory = db.query(InventorySummary).filter(
            InventorySummary.product_id == product.id
        ).first()
        current_stock = inventory.current_stock if inventory else 0

        # 计算建议采购量
        suggested_qty = max(0, item.quantity - current_stock)

        groups_dict[product.supplier_id].append({
            'product': product,
            'sales_quantity': item.quantity,
            'current_stock': current_stock,
            'suggested_quantity': suggested_qty
        })

    # 构建分组响应
    groups = []
    total_amount = 0

    for supplier_id, items in groups_dict.items():
        # 获取供应商名称
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        supplier_name = supplier.name if supplier else f'供应商{supplier_id}'

        group_items = []
        group_total = 0

        for item_data in items:
            product = item_data['product']
            group_items.append(PurchaseSuggestionItem(
                product_id=product.id,
                product_name=product.name,
                product_model=product.model,
                sales_quantity=item_data['sales_quantity'],
                current_stock=item_data['current_stock'],
                suggested_quantity=item_data['suggested_quantity'],
                purchase_price=product.purchase_price or 0,
                supplier_id=supplier_id,
                supplier_name=supplier_name
            ))
            group_total += item_data['suggested_quantity'] * (product.purchase_price or 0)

        groups.append(PurchaseSuggestionGroup(
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            items=group_items,
            total_amount=group_total
        ))
        total_amount += group_total

    return PurchaseSuggestionResponse(
        sales_order_id=order.id,
        sales_order_no=order.id,
        order_date=order.order_date,
        customer_name=order.customer.name if order.customer else None,
        groups=groups,
        total_amount=total_amount
    )
