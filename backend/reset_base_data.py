"""
重置数据库基础数据脚本
删除并重新创建客户、供应商、商品表的数据，保留其他表数据

使用说明：
    python reset_base_data.py

功能：
    1. 删除客户、供应商、商品相关表的数据
    2. 重新插入测试数据
    3. 重置相关表的自增 ID 起始值
"""
from sqlalchemy import text
from app.database import SessionLocal, engine, Base
from test_data import generate_base_data, BASE_DATA_ID_START


# 需要清空数据的表（按外键依赖顺序）
TABLES_TO_CLEAR = [
    "inventory_records",  # 先清空库存流水（依赖商品）
    "inventory_summary",  # 再清空库存汇总（依赖商品）
    "products",           # 商品表
    "suppliers",          # 供应商表
    "customers",          # 客户表
]

# 需要重置自增 ID 的表
AUTOINCREMENT_TABLES = [
    "customers",
    "suppliers",
    "products",
    "inventory_records",
    "inventory_summary"
]

# ID 起始值（从 12600000 开始，与 test_data.py 保持一致）
ID_START_VALUE = 12599999


def reset_base_data():
    """重置基础数据"""
    print("=" * 50)
    print("开始重置基础数据...")
    print("=" * 50)

    db = SessionLocal()
    try:
        # 1. 创建所有表（如果不存在）
        print("\n[1/4] 检查并创建数据表...")
        Base.metadata.create_all(bind=engine)
        print("✓ 数据表创建完成")

        # 2. 清空现有数据
        print("\n[2/4] 清空现有数据...")
        for table_name in TABLES_TO_CLEAR:
            db.execute(text(f"DELETE FROM {table_name}"))
            print(f"  - 已清空 {table_name} 表")
        db.commit()
        print("✓ 数据清空完成")

        # 3. 插入测试数据
        print("\n[3/4] 插入测试数据...")
        stats = generate_base_data(db, id_start=BASE_DATA_ID_START, initial_stock=100)
        print("✓ 测试数据插入完成")

        # 4. 重置自增 ID 起始值
        print("\n[4/4] 重置自增 ID 起始值...")
        for table_name in AUTOINCREMENT_TABLES:
            db.execute(text(f"UPDATE sqlite_sequence SET seq = {ID_START_VALUE} WHERE name = '{table_name}'"))
            print(f"  - {table_name} 表 ID 起始值已重置为 {ID_START_VALUE}")
        db.commit()
        print("✓ ID 起始值重置完成")

        print("\n" + "=" * 50)
        print("✓ 重置基础数据完成！")
        print("=" * 50)
        print("\n测试数据概览:")
        print(f"  - 客户：{stats['customers']} 个")
        print(f"  - 供应商：{stats['suppliers']} 个")
        print(f"  - 商品：{stats['products']} 个")
        print(f"  - 初始库存：每种商品 {stats['initial_stock']} 件")

    except Exception as e:
        print(f"\n✗ 操作失败：{e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("\n⚠️  警告：此操作将删除所有客户、供应商、商品数据！")
    print("   系统将保留用户、订单、发票等其他数据。\n")

    response = input("确认继续？(输入 yes 继续，其他取消): ")
    if response.lower() != "yes":
        print("操作已取消")
        exit(0)

    reset_base_data()
