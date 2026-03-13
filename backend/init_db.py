"""
初始化数据库脚本

功能：
    1. 创建数据库表
    2. 创建管理员账号

使用说明：
    python init_db.py
"""
from sqlalchemy import text
from app.database import SessionLocal, engine, Base
from app.models import User
from app.utils import get_password_hash


# 所有需要设置起始 ID 的表
AUTOINCREMENT_TABLES = [
    "users", "customers", "suppliers", "products",
    "sales_orders", "sales_order_items", "inventory_records",
    "import_error_logs", "invoices", "invoice_items",
    "purchase_orders", "purchase_order_items", "purchase_invoice_items",
    "inventory_summary"
]

# ID 起始值
ID_START_VALUE = 26030000


def init_db():
    """初始化数据库"""
    print("=" * 50)
    print("开始初始化数据库...")
    print("=" * 50)

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. 设置所有表的自增 ID 起始值
        print("\n[1/3] 设置自增 ID 起始值...")
        for table_name in AUTOINCREMENT_TABLES:
            db.execute(text(f"INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES ('{table_name}', {ID_START_VALUE - 1})"))
        db.commit()
        print(f"✓ ID 起始值已设置为 {ID_START_VALUE}")

        # 2. 创建管理员账号
        print("\n[2/3] 创建管理员账号...")
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                name="管理员"
            )
            db.add(admin)
            db.commit()
            print("✓ 管理员账号创建成功：用户名=admin, 密码=admin123")
        else:
            print("✓ 管理员账号已存在")

        print("\n" + "=" * 50)
        print("✓ 数据库初始化完成！")
        print("=" * 50)
        print("\n提示：如需生成测试数据，请运行:")
        print("  python3 init_test_data.py  - 生成基础测试数据（客户、供应商、商品）")
        print("  python3 reset_base_data.py - 重置并生成测试数据（含初始库存）")

    except Exception as e:
        print(f"\n✗ 初始化失败：{e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
