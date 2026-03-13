"""
设置数据库所有表的自增 ID 起始值为 2603000000
"""
from sqlalchemy import text
from app.database import SessionLocal, engine, Base


# 所有需要设置起始 ID 的表
AUTOINCREMENT_TABLES = [
    "users", "customers", "suppliers", "products",
    "sales_orders", "sales_order_items", "inventory_records",
    "import_error_logs", "invoices", "invoice_items",
    "purchase_orders", "purchase_order_items", "purchase_invoice_items",
    "sales_order_item_invoices", "payment_records"
]

# ID 起始值
ID_START_VALUE = 2603000000


def set_autoincrement_start():
    """设置所有自增表的 ID 起始值"""
    # 确保所有表已创建
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 设置所有自增表的起始 ID
        for table_name in AUTOINCREMENT_TABLES:
            db.execute(text(f"UPDATE sqlite_sequence SET seq = {ID_START_VALUE} WHERE name = '{table_name}'"))
        db.commit()
        print(f"✓ 设置所有表 ID 起始值为 {ID_START_VALUE}")
        print(f"  - 共设置 {len(AUTOINCREMENT_TABLES)} 个表")
    except Exception as e:
        print(f"✗ 设置失败：{e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    set_autoincrement_start()
