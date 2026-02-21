from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models import InventoryRecord, InventorySummary, Product, User
from app.schemas import InventoryRecordCreate, InventoryRecordResponse, InventorySummaryResponse
from app.utils import get_current_user

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
            "current_stock": summary.current_stock
        })
    return result

@router.get("/records", response_model=List[InventoryRecordResponse])
def get_inventory_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = db.query(InventoryRecord).offset(skip).limit(limit).order_by(InventoryRecord.created_at.desc()).all()
    result = []
    for record in records:
        result.append({
            "id": record.id,
            "product_id": record.product_id,
            "product_name": record.product.name if record.product else None,
            "product_model": record.product.model if record.product else None,
            "type": record.type,
            "quantity": record.quantity,
            "related_order_id": record.related_order_id,
            "created_at": record.created_at
        })
    return result

@router.post("/in", response_model=InventoryRecordResponse)
def create_inventory_in(record: InventoryRecordCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if record.type != "IN":
        raise HTTPException(status_code=400, detail="类型必须为IN")
    
    product = db.query(Product).filter(Product.id == record.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 创建库存流水
    db_record = InventoryRecord(
        product_id=record.product_id,
        type="IN",
        quantity=record.quantity,
        related_order_id=record.related_order_id
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
        "type": db_record.type,
        "quantity": db_record.quantity,
        "related_order_id": db_record.related_order_id,
        "created_at": db_record.created_at
    }
