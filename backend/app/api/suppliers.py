from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import Supplier, User
from app.schemas import SupplierCreate, SupplierUpdate, SupplierResponse, PaginatedSuppliersResponse
from app.utils import get_current_user

router = APIRouter()


@router.get("/", response_model=PaginatedSuppliersResponse)
def get_suppliers(
    skip: int = 0,
    limit: int = 15,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Supplier)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Supplier.name.ilike(search_pattern)) |
            (Supplier.contact.ilike(search_pattern)) |
            (Supplier.phone.ilike(search_pattern)) |
            (Supplier.email.ilike(search_pattern))
        )

    total = query.count()
    suppliers = query.order_by(Supplier.id.desc()).offset(skip).limit(limit).all()
    return {"items": suppliers, "total": total}


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    return supplier


@router.post("/", response_model=SupplierResponse)
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 检查供应商名称是否已存在
    existing = db.query(Supplier).filter(Supplier.name == supplier.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="供应商名称已存在")
    db_supplier = Supplier(**supplier.dict())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(supplier_id: int, supplier: SupplierUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not db_supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")

    # 检查名称是否与其他供应商重复
    update_data = supplier.dict(exclude_unset=True)
    if 'name' in update_data and update_data['name']:
        existing = db.query(Supplier).filter(
            Supplier.id != supplier_id,
            Supplier.name == update_data['name']
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="供应商名称已存在")

    for field, value in update_data.items():
        setattr(db_supplier, field, value)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not db_supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")

    # 检查是否有关联的商品
    if db_supplier.products:
        raise HTTPException(status_code=400, detail="该供应商下有商品，无法删除")

    db.delete(db_supplier)
    db.commit()
    return {"message": "删除成功"}