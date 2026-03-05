from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import Product, Supplier, User
from app.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.utils import get_current_user

router = APIRouter()


class PaginatedProductsResponse(BaseModel):
    items: List[ProductResponse]
    total: int


@router.get("/", response_model=PaginatedProductsResponse)
def get_products(
    skip: int = 0,
    limit: int = 15,
    search: Optional[str] = None,
    name: Optional[str] = None,
    model: Optional[str] = None,
    brand: Optional[str] = None,
    supplier_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Product).options(joinedload(Product.supplier))

    # 如果有 search 参数，在商品名称、型号、品牌中模糊搜索
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search_pattern)) |
            (Product.model.ilike(search_pattern)) |
            (Product.brand.ilike(search_pattern))
        )

    # 如果有 name 参数，按商品名称过滤
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))

    # 如果有 model 参数，按型号过滤
    if model:
        query = query.filter(Product.model.ilike(f"%{model}%"))

    # 如果有 brand 参数，按品牌过滤
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))

    # 按供应商ID筛选
    if supplier_id is not None:
        query = query.filter(Product.supplier_id == supplier_id)

    # 按零售价区间筛选
    if min_price is not None:
        query = query.filter(Product.retail_price >= min_price)
    if max_price is not None:
        query = query.filter(Product.retail_price <= max_price)

    total = query.count()
    products = query.offset(skip).limit(limit).all()

    # 转换结果以包含 supplier_name
    result = []
    for p in products:
        item = {
            "id": p.id,
            "name": p.name,
            "model": p.model,
            "brand": p.brand,
            "unit": p.unit,
            "tax_rate": p.tax_rate,
            "purchase_price": p.purchase_price,
            "retail_price": p.retail_price,
            "supplier_id": p.supplier_id,
            "supplier_name": p.supplier.name if p.supplier else None,
            "created_at": p.created_at
        }
        result.append(item)

    return {"items": result, "total": total}


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.query(Product).options(joinedload(Product.supplier)).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return {
        "id": product.id,
        "name": product.name,
        "model": product.model,
        "brand": product.brand,
        "unit": product.unit,
        "tax_rate": product.tax_rate,
        "purchase_price": product.purchase_price,
        "retail_price": product.retail_price,
        "supplier_id": product.supplier_id,
        "supplier_name": product.supplier.name if product.supplier else None,
        "created_at": product.created_at
    }


@router.post("/", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 检查品牌+型号联合唯一
    brand_value = product.brand or ""
    existing = db.query(Product).filter(
        Product.brand == brand_value,
        Product.model == product.model
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="相同品牌下该型号已存在")

    # 验证 supplier_id 是否存在
    if product.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=400, detail="供应商不存在")

    db_product = Product(**product.dict(exclude_unset=True))
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return {
        "id": db_product.id,
        "name": db_product.name,
        "model": db_product.model,
        "brand": db_product.brand,
        "unit": db_product.unit,
        "tax_rate": db_product.tax_rate,
        "purchase_price": db_product.purchase_price,
        "retail_price": db_product.retail_price,
        "supplier_id": db_product.supplier_id,
        "supplier_name": db_product.supplier.name if db_product.supplier else None,
        "created_at": db_product.created_at
    }


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="商品不存在")

    # 检查品牌+型号联合唯一（排除自身）
    update_data = product.dict(exclude_unset=True)
    new_brand = update_data.get('brand', db_product.brand) or ""
    new_model = update_data.get('model', db_product.model)

    # 检查是否有其他商品使用相同的 brand+model
    existing = db.query(Product).filter(
        Product.id != product_id,
        Product.brand == new_brand,
        Product.model == new_model
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="相同品牌下该型号已存在")

    # 验证 supplier_id 是否存在
    if 'supplier_id' in update_data and update_data['supplier_id']:
        supplier = db.query(Supplier).filter(Supplier.id == update_data['supplier_id']).first()
        if not supplier:
            raise HTTPException(status_code=400, detail="供应商不存在")

    for field, value in update_data.items():
        setattr(db_product, field, value)
    db.commit()
    db.refresh(db_product)

    return {
        "id": db_product.id,
        "name": db_product.name,
        "model": db_product.model,
        "brand": db_product.brand,
        "unit": db_product.unit,
        "tax_rate": db_product.tax_rate,
        "purchase_price": db_product.purchase_price,
        "retail_price": db_product.retail_price,
        "supplier_id": db_product.supplier_id,
        "supplier_name": db_product.supplier.name if db_product.supplier else None,
        "created_at": db_product.created_at
    }


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="商品不存在")
    db.delete(db_product)
    db.commit()
    return {"message": "删除成功"}