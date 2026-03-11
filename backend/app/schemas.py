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
    contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class CustomerResponse(BaseModel):
    id: int
    name: str
    contact: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class PaginatedCustomersResponse(BaseModel):
    items: List[CustomerResponse]
    total: int

# 供应商相关
class SupplierCreate(BaseModel):
    name: str
    contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    remark: Optional[str] = None

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    remark: Optional[str] = None

class SupplierResponse(BaseModel):
    id: int
    name: str
    contact: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    remark: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class PaginatedSuppliersResponse(BaseModel):
    items: List[SupplierResponse]
    total: int

# 商品相关
class ProductCreate(BaseModel):
    name: str
    model: str
    brand: Optional[str] = None
    unit: str = "件"
    tax_rate: float = 0.13
    purchase_price: float = 0
    retail_price: float = 0
    supplier_id: Optional[int] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    unit: Optional[str] = None
    tax_rate: Optional[float] = None
    purchase_price: Optional[float] = None
    retail_price: Optional[float] = None
    supplier_id: Optional[int] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    model: str
    brand: Optional[str]
    unit: str
    tax_rate: float
    purchase_price: float
    retail_price: float
    supplier_id: Optional[int]
    supplier_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# 销售订单相关
class SalesOrderItemCreate(BaseModel):
    product_id: int
    customer_product_code: Optional[str] = None  # 客户商品编号
    quantity: float
    unit_price_tax: float  # 含税单价
    discounted_price_tax: float  # 含税优惠价
    discount_rate: float = 0  # 折扣率（只读）

class SalesOrderItemResponse(BaseModel):
    id: int
    product_id: int
    customer_product_code: Optional[str] = None  # 客户商品编号
    product_name: Optional[str] = None
    product_model: Optional[str] = None
    quantity: float
    unit_price_tax: float  # 含税单价
    discounted_price_tax: float  # 含税优惠价
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
    contract_no: Optional[str] = None  # 合同编号
    contract_date: Optional[datetime] = None  # 合同日期
    contract_amount: Optional[float] = None
    payment_status: str = "未付款"
    items: List[SalesOrderItemCreate]

class SalesOrderResponse(BaseModel):
    id: int
    order_date: datetime
    customer_id: int
    customer_name: Optional[str] = None
    salesperson_id: int
    salesperson_name: Optional[str] = None
    contract_no: Optional[str] = None  # 合同编号
    contract_date: Optional[datetime] = None  # 合同日期
    contract_amount: Optional[float] = 0.0
    payment_status: str
    total_amount: Optional[float] = 0.0
    paid_amount: Optional[float] = 0.0  # 已付金额
    unpaid_amount: Optional[float] = 0.0  # 未付金额（计算字段）
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


# 发票相关
class InvoiceItemCreate(BaseModel):
    order_id: int
    order_item_id: Optional[int] = None  # 订单商品明细ID
    amount: float
    tax_amount: float = 0


class ProductItemForInvoice(BaseModel):
    """发票关联订单的商品明细"""
    id: int
    order_item_id: int
    product_id: int
    product_name: Optional[str] = None
    product_model: Optional[str] = None
    quantity: float
    unit_price: float
    amount: float
    tax_amount: float


class InvoiceItemResponse(BaseModel):
    id: int
    invoice_id: int
    order_id: int
    order_item_id: Optional[int] = None
    order_no: int
    order_date: Optional[datetime] = None
    customer_name: Optional[str] = None
    order_total_amount: Optional[float] = None
    contract_amount: Optional[float] = None
    amount: float
    tax_amount: float
    product_items: List[ProductItemForInvoice] = []

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    invoice_no: str
    invoice_date: datetime
    customer_id: int
    total_amount: float
    tax_amount: float = 0
    remark: Optional[str] = None
    items: List[InvoiceItemCreate]


class InvoiceResponse(BaseModel):
    id: int
    invoice_no: str
    invoice_date: datetime
    customer_id: int
    customer_name: Optional[str] = None
    total_amount: float
    tax_amount: float
    status: str
    remark: Optional[str] = None
    created_by: int
    creator_name: Optional[str] = None
    created_at: datetime
    items: List[InvoiceItemResponse] = []

    class Config:
        from_attributes = True


class PaginatedInvoicesResponse(BaseModel):
    items: List[dict]
    total: int


class OrderInvoiceInfo(BaseModel):
    order_id: int
    order_no: int
    order_date: datetime
    total_amount: float
    invoiced_amount: float  # 已开票金额
    balance_amount: float  # 可开票余额


# ==================== 收款记录相关 ====================

class PaymentRecordCreate(BaseModel):
    """创建收款记录"""
    order_id: int
    amount: float
    payment_date: datetime
    payment_method: str = "银行转账"
    remark: Optional[str] = None


class PaymentRecordResponse(BaseModel):
    """收款记录响应"""
    id: int
    order_id: int
    amount: float
    payment_date: datetime
    payment_method: str
    remark: Optional[str]
    created_by: int
    creator_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentRecordListResponse(BaseModel):
    """收款记录列表（含订单信息）"""
    id: int
    order_id: int
    order_no: Optional[int] = None  # 订单号
    customer_name: Optional[str] = None  # 客户名称
    order_total_amount: Optional[float] = None  # 订单总金额
    order_paid_amount: Optional[float] = None  # 订单已付金额
    order_unpaid_amount: Optional[float] = None  # 订单未付金额
    amount: float
    payment_date: datetime
    payment_method: str
    remark: Optional[str]
    created_by: int
    creator_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 采购订单相关 ====================

class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    quantity: float
    unit_price: float


class PurchaseOrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    product_model: Optional[str] = None
    quantity: float
    unit_price: float
    received_quantity: float
    unreceived_quantity: float  # 未入库数量
    line_total: float

    class Config:
        from_attributes = True


class PurchaseOrderCreate(BaseModel):
    order_date: datetime
    supplier_id: int
    remark: Optional[str] = None
    items: List[PurchaseOrderItemCreate]


class PurchaseOrderResponse(BaseModel):
    id: int
    order_date: datetime
    supplier_id: int
    supplier_name: Optional[str] = None
    purchaser_id: int
    purchaser_name: Optional[str] = None
    total_amount: float
    status: str
    remark: Optional[str] = None
    created_at: datetime
    items: List[PurchaseOrderItemResponse] = []

    class Config:
        from_attributes = True


class PaginatedPurchaseOrdersResponse(BaseModel):
    items: List[dict]
    total: int


class PurchaseOrderInvoiceInfo(BaseModel):
    order_id: int
    order_no: int
    order_date: datetime
    total_amount: float
    invoiced_amount: float  # 已开票金额
    balance_amount: float  # 可开票余额


# ==================== 订单商品明细开票相关 ====================

class SalesOrderItemForInvoice(BaseModel):
    """订单商品明细（用于开票）"""
    id: int
    product_id: int
    product_name: Optional[str] = None
    product_model: Optional[str] = None
    quantity: float  # 订单数量
    invoiced_quantity: float = 0  # 已开票数量
    available_quantity: float  # 可开票数量
    discounted_price_tax: float  # 含税优惠价
    line_total: float  # 订单小计
    available_amount: float  # 可开票金额

    class Config:
        from_attributes = True


class OrderInvoiceSummary(BaseModel):
    """订单可开票汇总"""
    order_id: int
    order_no: int
    order_date: datetime
    customer_name: Optional[str] = None
    total_amount: float  # 订单总金额
    invoiced_amount: float  # 已开票金额
    balance_amount: float  # 可开票余额
    items: List[SalesOrderItemForInvoice] = []


class InvoiceItemCreateFromOrder(BaseModel):
    """从订单创建发票明细"""
    order_item_id: int
    quantity: float  # 本次开票数量
    amount: float  # 本次开票金额（含税）
    tax_amount: float = 0  # 本次税额


class InvoiceCreateFromOrder(BaseModel):
    """从订单创建发票"""
    invoice_no: str
    invoice_date: datetime
    customer_id: int
    remark: Optional[str] = None
    items: List[InvoiceItemCreateFromOrder]