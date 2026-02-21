from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import SalesOrder, SalesOrderItem, Product, Customer, User, InventoryRecord, InventorySummary
from app.schemas import SalesOrderCreate, SalesOrderResponse, SalesOrderItemResponse
from app.utils import get_current_user
from datetime import datetime

router = APIRouter()

def calculate_order_amounts(items_data):
    """计算订单金额"""
    total = 0
    calculated_items = []
    for item in items_data:
        final_price = item["unit_price_tax"] * (1 - item.get("discount_rate", 0))
        line_total = item["quantity"] * final_price
        total += line_total
        calculated_items.append({
            **item,
            "final_unit_price_tax": final_price,
            "line_total": line_total,
            "unshipped_quantity": item["quantity"]
        })
    return calculated_items, total

@router.get("/", response_model=List[SalesOrderResponse])
def get_sales_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    orders = db.query(SalesOrder).offset(skip).limit(limit).order_by(SalesOrder.order_date.desc()).all()
    result = []
    for order in orders:
        order_dict = {
            "id": order.id,
            "order_date": order.order_date,
            "customer_id": order.customer_id,
            "customer_name": order.customer.name if order.customer else None,
            "salesperson_id": order.salesperson_id,
            "salesperson_name": order.salesperson.name if order.salesperson else None,
            "contract_amount": order.contract_amount,
            "payment_status": order.payment_status,
            "total_amount": order.total_amount,
            "created_at": order.created_at,
            "items": []
        }
        for item in order.items:
            order_dict["items"].append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name if item.product else None,
                "product_model": item.product.model if item.product else None,
                "quantity": item.quantity,
                "unit_price_tax": item.unit_price_tax,
                "discount_rate": item.discount_rate,
                "final_unit_price_tax": item.final_unit_price_tax,
                "line_total": item.line_total,
                "shipped_quantity": item.shipped_quantity,
                "unshipped_quantity": item.unshipped_quantity
            })
        result.append(order_dict)
    return result

@router.get("/{order_id}", response_model=SalesOrderResponse)
def get_sales_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return {
        "id": order.id,
        "order_date": order.order_date,
        "customer_id": order.customer_id,
        "customer_name": order.customer.name if order.customer else None,
        "salesperson_id": order.salesperson_id,
        "salesperson_name": order.salesperson.name if order.salesperson else None,
        "contract_amount": order.contract_amount,
        "payment_status": order.payment_status,
        "total_amount": order.total_amount,
        "created_at": order.created_at,
        "items": [{
            "id": item.id,
            "product_id": item.product_id,
            "product_name": item.product.name if item.product else None,
            "product_model": item.product.model if item.product else None,
            "quantity": item.quantity,
            "unit_price_tax": item.unit_price_tax,
            "discount_rate": item.discount_rate,
            "final_unit_price_tax": item.final_unit_price_tax,
            "line_total": item.line_total,
            "shipped_quantity": item.shipped_quantity,
            "unshipped_quantity": item.unshipped_quantity
        } for item in order.items]
    }

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
            raise HTTPException(status_code=404, detail=f"商品ID {item_data['product_id']} 不存在")
        
        db_item = SalesOrderItem(
            order_id=db_order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            unit_price_tax=item_data["unit_price_tax"],
            discount_rate=item_data.get("discount_rate", 0),
            final_unit_price_tax=item_data["final_unit_price_tax"],
            line_total=item_data["line_total"],
            shipped_quantity=0,
            unshipped_quantity=item_data["unshipped_quantity"]
        )
        db.add(db_item)
        
        # 生成库存OUT流水
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
            raise HTTPException(status_code=404, detail=f"商品ID {item_data['product_id']} 不存在")
        
        db_item = SalesOrderItem(
            order_id=db_order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            unit_price_tax=item_data["unit_price_tax"],
            discount_rate=item_data.get("discount_rate", 0),
            final_unit_price_tax=item_data["final_unit_price_tax"],
            line_total=item_data["line_total"],
            shipped_quantity=0,
            unshipped_quantity=item_data["unshipped_quantity"]
        )
        db.add(db_item)
        
        # 生成库存OUT流水
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
    
    # 删除订单（级联删除明细）
    db.delete(db_order)
    db.commit()
    return {"message": "删除成功"}
