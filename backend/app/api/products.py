from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Product, User
from app.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.utils import get_current_user

router = APIRouter()

@router.get("/", response_model=List[ProductResponse])
def get_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    name: Optional[str] = None,
    model: Optional[str] = None,
    brand: Optional[str] = None,
    supplier: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Product)

    # 如果有 search 参数，在商品名称、型号、品牌、供应商中模糊搜索
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search_pattern)) |
            (Product.model.ilike(search_pattern)) |
            (Product.brand.ilike(search_pattern)) |
            (Product.supplier.ilike(search_pattern))
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

    # 如果有 supplier 参数，按供应商过滤
    if supplier:
        query = query.filter(Product.supplier.ilike(f"%{supplier}%"))

    # 按零售价区间筛选
    if min_price is not None:
        query = query.filter(Product.retail_price >= min_price)
    if max_price is not None:
        query = query.filter(Product.retail_price <= max_price)

    products = query.offset(skip).limit(limit).all()
    return products

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return product

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
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

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

    for field, value in update_data.items():
        setattr(db_product, field, value)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="商品不存在")
    db.delete(db_product)
    db.commit()
    return {"message": "删除成功"}
