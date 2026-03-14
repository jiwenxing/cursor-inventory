from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, date
from app.api import auth, customers, suppliers, products, sales_orders, inventory, import_excel, statistics, invoices, purchase_orders, payment_records
from app.database import engine, Base
from app.timezone import to_cst_datetime
import logging
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class CustomJSONResponse(JSONResponse):
    """自定义 JSON 响应，自动处理 datetime 时区转换"""
    media_type = "application/json"

    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=self._default_encoder,
        ).encode("utf-8")

    def _default_encoder(self, obj):
        """自定义 JSON 编码器，处理 datetime 对象"""
        if isinstance(obj, datetime):
            return to_cst_datetime(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


app = FastAPI(
    title="进销存系统",
    version="1.0.0",
    default_response_class=CustomJSONResponse,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CustomJSONResponse(JSONResponse):
    """自定义 JSON 响应，自动处理 datetime 时区转换"""
    media_type = "application/json"

    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=self._default_encoder,
        ).encode("utf-8")

    def _default_encoder(self, obj):
        """自定义 JSON 编码器，处理 datetime 对象"""
        if isinstance(obj, datetime):
            return to_cst_datetime(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(customers.router, prefix="/api/customers", tags=["客户管理"])
app.include_router(suppliers.router, prefix="/api/suppliers", tags=["供应商管理"])
app.include_router(products.router, prefix="/api/products", tags=["商品管理"])
app.include_router(sales_orders.router, prefix="/api/sales-orders", tags=["销售订单"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["发票管理"])
app.include_router(purchase_orders.router, prefix="/api/purchase-orders", tags=["采购订单"])
app.include_router(payment_records.router, prefix="/api/payment-records", tags=["收款记录"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["库存管理"])
app.include_router(import_excel.router, prefix="/api/import", tags=["Excel导入"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["统计报表"])

@app.on_event("startup")
async def startup():
    # 创建数据库表
    Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "进销存系统API"}