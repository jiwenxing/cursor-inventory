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

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    contact = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    address = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    orders = relationship("SalesOrder", back_populates="customer")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    contact = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    address = Column(Text)
    remark = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    products = relationship("Product", back_populates="supplier")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint('brand', 'model', name='uq_brand_model'),
    )

    id = Column(Integer, primary_key=True, index=True)
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
    inventory_records = relationship("InventoryRecord", back_populates="product")
    inventory_summary = relationship("InventorySummary", back_populates="product", uselist=False)

class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_date = Column(DateTime, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    salesperson_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_amount = Column(Float, default=0)
    payment_status = Column(String(20), default=PaymentStatus.UNPAID.value)
    total_amount = Column(Float, default=0)
    created_at = Column(DateTime, server_default=func.now())

    customer = relationship("Customer", back_populates="orders")
    salesperson = relationship("User")
    items = relationship("SalesOrderItem", back_populates="order", cascade="all, delete-orphan")
    invoice_items = relationship("InvoiceItem", back_populates="order")

class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price_tax = Column(Float, nullable=False)
    discount_rate = Column(Float, default=0)  # 支持负数
    final_unit_price_tax = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)
    shipped_quantity = Column(Float, default=0)
    unshipped_quantity = Column(Float, nullable=False)

    order = relationship("SalesOrder", back_populates="items")
    product = relationship("Product", back_populates="order_items")

class InventoryRecord(Base):
    __tablename__ = "inventory_records"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    type = Column(String(10), nullable=False)  # IN / OUT
    quantity = Column(Float, nullable=False)
    related_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    product = relationship("Product", back_populates="inventory_records")
    related_order = relationship("SalesOrder")

class InventorySummary(Base):
    __tablename__ = "inventory_summary"

    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    current_stock = Column(Float, default=0, nullable=False)

    product = relationship("Product", back_populates="inventory_summary")

class ImportErrorLog(Base):
    __tablename__ = "import_error_logs"

    id = Column(Integer, primary_key=True, index=True)
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

    id = Column(Integer, primary_key=True, index=True)
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


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)  # 发票ID
    order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)  # 关联的订单ID
    order_no = Column(Integer, nullable=False)  # 订单号（冗余）
    amount = Column(Float, nullable=False)  # 本次开票金额
    tax_amount = Column(Float, default=0)  # 本次税额

    invoice = relationship("Invoice", back_populates="items")
    order = relationship("SalesOrder")