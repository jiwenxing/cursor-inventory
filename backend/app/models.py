from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class PaymentStatus(str, enum.Enum):
    UNPAID = "未付款"
    PARTIAL = "部分付款"
    PAID = "已付款"

class InventoryType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    contact = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    address = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    orders = relationship("SalesOrder", back_populates="customer")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    contact = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    address = Column(Text)
    remark = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    products = relationship("Product", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint('brand', 'model', name='uq_brand_model'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    model = Column(String(100), nullable=False, index=True)
    brand = Column(String(100))
    unit = Column(String(20), default="件")
    tax_rate = Column(Float, default=0.13)  # 默认税率13%
    purchase_price = Column(Float, default=0)  # 采购价
    retail_price = Column(Float, default=0)  # 零售价/销售价
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    supplier = relationship("Supplier", back_populates="products")
    order_items = relationship("SalesOrderItem", back_populates="product")
    purchase_order_items = relationship("PurchaseOrderItem", back_populates="product")
    inventory_records = relationship("InventoryRecord", back_populates="product")
    inventory_summary = relationship("InventorySummary", back_populates="product", uselist=False)

class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_date = Column(DateTime, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    salesperson_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_no = Column(String(100))  # 合同编号
    contract_date = Column(DateTime)  # 合同日期
    contract_amount = Column(Float, default=0)
    payment_status = Column(String(20), default=PaymentStatus.UNPAID.value)
    total_amount = Column(Float, default=0)
    paid_amount = Column(Float, default=0)  # 已付金额
    created_at = Column(DateTime, server_default=func.now())

    customer = relationship("Customer", back_populates="orders")
    salesperson = relationship("User")
    items = relationship("SalesOrderItem", back_populates="order", cascade="all, delete-orphan")
    invoice_items = relationship("InvoiceItem", back_populates="order")
    payment_records = relationship("PaymentRecord", back_populates="order", cascade="all, delete-orphan")

class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    customer_product_code = Column(String(100))  # 客户商品编号
    quantity = Column(Float, nullable=False)
    unit_price_tax = Column(Float, nullable=False)  # 含税单价
    discounted_price_tax = Column(Float, nullable=False)  # 含税优惠价
    discount_rate = Column(Float, default=0)  # 折扣率（只读，由含税优惠价/含税单价计算）
    final_unit_price_tax = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)
    shipped_quantity = Column(Float, default=0)
    unshipped_quantity = Column(Float, nullable=False)

    order = relationship("SalesOrder", back_populates="items")
    product = relationship("Product", back_populates="order_items")

class InventoryRecord(Base):
    __tablename__ = "inventory_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    type = Column(String(10), nullable=False)  # IN / OUT
    quantity = Column(Float, nullable=False)
    related_order_id = Column(Integer, nullable=True)  # 关联订单 ID（销售订单或采购订单）
    related_order_type = Column(String(20), nullable=True)  # "sales" 或 "purchase"
    created_at = Column(DateTime, server_default=func.now(), index=True)

    product = relationship("Product", back_populates="inventory_records")

class InventorySummary(Base):
    __tablename__ = "inventory_summary"

    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    current_stock = Column(Float, default=0, nullable=False)

    product = relationship("Product", back_populates="inventory_summary")

class ImportErrorLog(Base):
    __tablename__ = "import_error_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    import_batch_id = Column(String(50), index=True)
    error_type = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=False)
    row_data = Column(Text)  # JSON格式存储异常行数据
    created_at = Column(DateTime, server_default=func.now())


class InvoiceStatus(str, enum.Enum):
    NORMAL = "已开票"
    CANCELLED = "已作废"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_no = Column(String(50), unique=True, nullable=False, index=True)  # 发票号
    invoice_date = Column(DateTime, nullable=False, index=True)  # 开票日期
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)  # 客户
    total_amount = Column(Float, nullable=False)  # 发票总金额（含税）
    tax_amount = Column(Float, default=0)  # 税额
    status = Column(String(20), default=InvoiceStatus.NORMAL.value)  # 状态
    remark = Column(Text)  # 备注
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # 开票人
    created_at = Column(DateTime, server_default=func.now())

    customer = relationship("Customer")
    creator = relationship("User")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    purchase_invoice_items = relationship("PurchaseInvoiceItem", back_populates="invoice", cascade="all, delete-orphan")  # 进项发票明细


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)  # 发票ID
    order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)  # 关联的订单ID
    order_item_id = Column(Integer, ForeignKey("sales_order_items.id"), nullable=True)  # 关联的订单商品明细ID
    order_no = Column(Integer, nullable=False)  # 订单号（冗余）
    amount = Column(Float, nullable=False)  # 本次开票金额
    tax_amount = Column(Float, default=0)  # 本次税额

    invoice = relationship("Invoice", back_populates="items")
    order = relationship("SalesOrder")
    order_item = relationship("SalesOrderItem")


class SalesOrderItemInvoice(Base):
    """订单商品明细开票记录表"""
    __tablename__ = "sales_order_item_invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_item_id = Column(Integer, ForeignKey("sales_order_items.id"), nullable=False)  # 订单商品明细ID
    invoice_item_id = Column(Integer, ForeignKey("invoice_items.id"), nullable=False)  # 发票明细ID
    invoiced_quantity = Column(Float, nullable=False)  # 本次开票数量
    invoiced_amount = Column(Float, nullable=False)  # 本次开票金额（含税）
    invoiced_tax_amount = Column(Float, default=0)  # 本次税额
    created_at = Column(DateTime, server_default=func.now())

    order_item = relationship("SalesOrderItem")
    invoice_item = relationship("InvoiceItem")


# ==================== 收款记录相关 ====================

class PaymentMethod(str, enum.Enum):
    """收款方式"""
    BANK_TRANSFER = "银行转账"
    CASH = "现金"
    ACCEPTANCE_BILL = "承兑汇票"
    CHECK = "支票"
    OTHER = "其他"


class PaymentRecord(Base):
    """收款记录表"""
    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False, index=True)  # 关联订单 ID
    amount = Column(Float, nullable=False)  # 收款金额
    payment_date = Column(DateTime, nullable=False)  # 收款日期
    payment_method = Column(String(20), default=PaymentMethod.BANK_TRANSFER.value)  # 收款方式
    remark = Column(Text)  # 备注
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # 创建人
    created_at = Column(DateTime, server_default=func.now())

    order = relationship("SalesOrder", back_populates="payment_records")
    creator = relationship("User")


# ==================== 采购订单相关 ====================

class PurchaseOrderStatus(str, enum.Enum):
    PENDING = "待入库"
    PARTIAL = "部分入库"
    COMPLETED = "已完成"


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_date = Column(DateTime, nullable=False, index=True)  # 订单日期
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)  # 供应商 ID
    purchaser_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 采购员 ID
    total_amount = Column(Float, default=0)  # 订单总金额
    status = Column(String(20), default=PurchaseOrderStatus.PENDING.value)  # 状态
    remark = Column(Text)  # 备注
    created_at = Column(DateTime, server_default=func.now())

    supplier = relationship("Supplier", back_populates="purchase_orders")
    purchaser = relationship("User")
    items = relationship("PurchaseOrderItem", back_populates="order", cascade="all, delete-orphan")
    invoice_items = relationship("PurchaseInvoiceItem", back_populates="order")  # 预留：进项发票关联


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)  # 订单 ID
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)  # 商品 ID
    quantity = Column(Float, nullable=False)  # 采购数量
    unit_price = Column(Float, nullable=False)  # 采购单价
    received_quantity = Column(Float, default=0)  # 已入库数量
    line_total = Column(Float, nullable=False)  # 小计金额

    order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product", back_populates="purchase_order_items")


class PurchaseInvoiceItem(Base):
    __tablename__ = "purchase_invoice_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)  # 进项发票 ID
    order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)  # 关联的采购订单 ID
    order_no = Column(Integer, nullable=False)  # 订单号（冗余）
    amount = Column(Float, nullable=False)  # 本次开票金额
    tax_amount = Column(Float, default=0)  # 本次税额

    invoice = relationship("Invoice", back_populates="purchase_invoice_items")
    order = relationship("PurchaseOrder")