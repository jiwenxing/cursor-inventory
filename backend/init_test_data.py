"""
初始化测试数据脚本

生成基础测试数据：客户、供应商、商品

使用说明：
    python init_test_data.py

功能：
    1. 检查数据库是否已初始化（是否存在管理员账号）
    2. 生成基础测试数据（客户、供应商、商品）
    3. 重置自增 ID 起始值
"""
from sqlalchemy import text
from app.database import SessionLocal, engine, Base
from app.models import User, Customer
from test_data import generate_base_data, BASE_DATA_ID_START


# 所有需要设置起始 ID 的表
AUTOINCREMENT_TABLES = [
    "users", "customers", "suppliers", "products"
]

# ID 起始值（从 12600000 开始）
ID_START_VALUE = 12599999


def init_test_data():
    """初始化测试数据"""
    print("=" * 50)
    print("开始初始化测试数据...")
    print("=" * 50)

    db = SessionLocal()
    try:
        # 1. 创建所有表（如果不存在）
        print("\n[1/3] 检查并创建数据库表...")
        Base.metadata.create_all(bind=engine)
        print("✓ 数据库表创建完成")

        # 2. 检查是否已初始化
        print("\n[2/3] 检查数据库状态...")
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("✗ 数据库未初始化，请先运行：python init_db.py")
            return

        if db.query(Customer).first():
            print("✓ 数据库已有测试数据，跳过生成")
            print("\n提示：如需重置测试数据，请运行：python reset_base_data.py")
            return

        # 3. 生成测试数据
        print("\n[3/3] 生成测试数据...")
        stats = generate_base_data(db, id_start=BASE_DATA_ID_START, initial_stock=0)

        # 重置自增 ID 起始值
        for table_name in AUTOINCREMENT_TABLES:
            db.execute(text(f"UPDATE sqlite_sequence SET seq = {ID_START_VALUE} WHERE name = '{table_name}'"))
        db.commit()
        print(f"✓ ID 起始值已重置为 {ID_START_VALUE}")

        print("\n" + "=" * 50)
        print("✓ 测试数据初始化完成！")
        print("=" * 50)
        print("\n数据概览:")
        print(f"  - 客户：{stats['customers']} 个")
        print(f"  - 供应商：{stats['suppliers']} 个")
        print(f"  - 商品：{stats['products']} 个")

    except Exception as e:
        print(f"\n✗ 初始化失败：{e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_test_data()
