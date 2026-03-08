"""
重置数据库基础数据脚本
删除并重新创建客户、供应商、商品表的数据，保留其他表数据

使用说明：
    python reset_base_data.py

功能：
    1. 删除客户、供应商、商品相关表的所有数据
    2. 重新插入测试数据
    3. 重置相关表的自增 ID 起始值
"""
from sqlalchemy import text
from app.database import SessionLocal, engine, Base
from app.models import Customer, Supplier, Product, InventoryRecord, InventorySummary
from datetime import datetime


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

# ID 起始值（从 12600000 开始，与 init_db.py 保持一致）
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
        insert_test_data(db)
        db.commit()
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
        print(f"  - 客户：8 个")
        print(f"  - 供应商：3 个")
        print(f"  - 商品：10 个")
        print(f"  - 初始库存：每种商品 100 件")

    except Exception as e:
        print(f"\n✗ 操作失败：{e}")
        db.rollback()
        raise
    finally:
        db.close()


def insert_test_data(db):
    """插入测试数据"""

    # 1. 创建客户
    customers = [
        Customer(name="杭州华为科技有限公司", contact="张经理", phone="13800138001", email="zhang@huawei.com", address="杭州市西湖区"),
        Customer(name="宁波吉利汽车", contact="李总", phone="13800138002", email="li@geely.com", address="宁波市北仑区"),
        Customer(name="温州正泰电器", contact="王主任", phone="13800138003", email="wang@chint.com", address="温州市乐清市"),
        Customer(name="绍兴海亮集团", contact="刘经理", phone="13800138004", email="liu@hangliang.com", address="绍兴市诸暨市"),
        Customer(name="金华绿源电动车", contact="陈总", phone="13800138005", email="chen@lvyuan.com", address="金华市婺城区"),
        Customer(name="台州星星集团", contact="周经理", phone="13800138006", email="zhou@xingxing.com", address="台州市椒江区"),
        Customer(name="嘉兴梦迪集团", contact="吴总", phone="13800138007", email="wu@mengdi.com", address="嘉兴市秀洲区"),
        Customer(name="湖州久盛电气", contact="郑工", phone="13800138008", email="zheng@jiusheng.com", address="湖州市南浔区"),
    ]
    for c in customers:
        db.add(c)
    db.flush()
    print(f"  ✓ 创建 {len(customers)} 个客户")

    # 2. 创建供应商
    suppliers = [
        Supplier(name="上海电气集团", contact="张经理", phone="021-12345678", email="shanghai@electric.com", address="上海市"),
        Supplier(name="苏州精密机械厂", contact="李工", phone="0512-87654321", email="suzhou@precision.com", address="苏州市"),
        Supplier(name="南京自动化公司", contact="王总", phone="025-11112222", email="nanjing@auto.com", address="南京市"),
    ]
    for s in suppliers:
        db.add(s)
    db.flush()
    print(f"  ✓ 创建 {len(suppliers)} 个供应商")

    # 3. 创建商品
    products = [
        Product(name="变频器", model="VFD-A", brand="松下", unit="台", tax_rate=0.13, purchase_price=800, retail_price=1200, supplier_id=suppliers[0].id),
        Product(name="PLC 控制器", model="PLC-200", brand="西门子", unit="台", tax_rate=0.13, purchase_price=2500, retail_price=3800, supplier_id=suppliers[0].id),
        Product(name="伺服电机", model="SM-100", brand="安川", unit="台", tax_rate=0.13, purchase_price=1500, retail_price=2200, supplier_id=suppliers[1].id),
        Product(name="触摸屏", model="HMI-7", brand="威纶", unit="台", tax_rate=0.13, purchase_price=600, retail_price=950, supplier_id=suppliers[1].id),
        Product(name="减速机", model="NMRV-30", brand="台邦", unit="台", tax_rate=0.13, purchase_price=400, retail_price=650, supplier_id=suppliers[2].id),
        Product(name="传感器", model="GZ-001", brand="倍加福", unit="个", tax_rate=0.13, purchase_price=80, retail_price=150, supplier_id=suppliers[2].id),
        Product(name="继电器", model="MY2N", brand="欧姆龙", unit="个", tax_rate=0.13, purchase_price=15, retail_price=28, supplier_id=suppliers[0].id),
        Product(name="断路器", model="NSX-100", brand="施耐德", unit="个", tax_rate=0.13, purchase_price=350, retail_price=520, supplier_id=suppliers[1].id),
        Product(name="接触器", model="LC1D32", brand="施耐德", unit="个", tax_rate=0.13, purchase_price=120, retail_price=190, supplier_id=suppliers[1].id),
        Product(name="按钮开关", model="XB2-EA", brand="施耐德", unit="个", tax_rate=0.13, purchase_price=8, retail_price=15, supplier_id=suppliers[2].id),
    ]
    for p in products:
        db.add(p)
    db.flush()
    print(f"  ✓ 创建 {len(products)} 个商品")

    # 4. 创建初始库存（每种商品 100 件）
    for p in products:
        # 创建入库记录
        record = InventoryRecord(
            product_id=p.id,
            type="IN",
            quantity=100,
            related_order_id=None,
            related_order_type=None
        )
        db.add(record)

        # 创建库存汇总
        summary = InventorySummary(product_id=p.id, current_stock=100)
        db.add(summary)
    db.flush()
    print(f"  ✓ 创建库存记录（每种商品 100 件）")


if __name__ == "__main__":
    print("\n⚠️  警告：此操作将删除所有客户、供应商、商品数据！")
    print("   系统将保留用户、订单、发票等其他数据。\n")

    response = input("确认继续？(输入 yes 继续，其他取消): ")
    if response.lower() != "yes":
        print("操作已取消")
        exit(0)

    reset_base_data()
    print("\n提示：如需重置并生成完整测试数据（含订单、发票），请运行：python init_db.py")
