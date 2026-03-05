from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, customers, suppliers, products, sales_orders, inventory, import_excel, statistics
from app.database import engine, Base
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="进销存系统", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(customers.router, prefix="/api/customers", tags=["客户管理"])
app.include_router(suppliers.router, prefix="/api/suppliers", tags=["供应商管理"])
app.include_router(products.router, prefix="/api/products", tags=["商品管理"])
app.include_router(sales_orders.router, prefix="/api/sales-orders", tags=["销售订单"])
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