from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# 用户相关
class UserCreate(BaseModel):
    username: str
    password: str
    name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    name: Optional[str]
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

# 客户相关
class CustomerCreate(BaseModel):
    name: str
    code: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CustomerResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    contact: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# 商品相关
class ProductCreate(BaseModel):
    name: str
    model: str
    brand: Optional[str] = None
    unit: str = "件"
    tax_rate: float = 0.13

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    unit: Optional[str] = None
    tax_rate: Optional[float] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    model: str
    brand: Optional[str]
    unit: str
    tax_rate: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# 销售订单相关
class SalesOrderItemCreate(BaseModel):
    product_id: int
    quantity: float
    unit_price_tax: float
    discount_rate: float = 0

class SalesOrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    product_model: Optional[str] = None
    quantity: float
    unit_price_tax: float
    discount_rate: float
    final_unit_price_tax: float
    line_total: float
    shipped_quantity: float
    unshipped_quantity: float
    
    class Config:
        from_attributes = True

class SalesOrderCreate(BaseModel):
    order_date: datetime
    customer_id: int
    contract_amount: float = 0
    payment_status: str = "未付款"
    items: List[SalesOrderItemCreate]

class SalesOrderResponse(BaseModel):
    id: int
    order_date: datetime
    customer_id: int
    customer_name: Optional[str] = None
    salesperson_id: int
    salesperson_name: Optional[str] = None
    contract_amount: float
    payment_status: str
    total_amount: float
    created_at: datetime
    items: List[SalesOrderItemResponse] = []
    
    class Config:
        from_attributes = True

# 库存相关
class InventoryRecordCreate(BaseModel):
    product_id: int
    type: str  # IN / OUT
    quantity: float
    related_order_id: Optional[int] = None

class InventoryRecordResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    product_model: Optional[str] = None
    type: str
    quantity: float
    related_order_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class InventorySummaryResponse(BaseModel):
    product_id: int
    product_name: Optional[str] = None
    product_model: Optional[str] = None
    current_stock: float
    
    class Config:
        from_attributes = True

# Excel导入相关
class ImportErrorLogResponse(BaseModel):
    id: int
    import_batch_id: str
    error_type: str
    error_message: str
    row_data: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ImportResult(BaseModel):
    success: bool
    total_rows: int
    success_rows: int
    error_rows: int
    errors: List[ImportErrorLogResponse] = []
    batch_id: str
