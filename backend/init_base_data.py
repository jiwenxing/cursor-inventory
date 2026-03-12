"""
初始化基础数据脚本
仅创建客户、供应商、商品数据，不创建订单和发票

使用说明：
    python init_base_data.py

功能：
    1. 创建数据库表（如果不存在）
    2. 创建管理员账号（如果不存在）
    3. 生成基础测试数据（客户、供应商、商品）
    4. 重置自增 ID 起始值
"""
from sqlalchemy import text
from app.database import SessionLocal, engine, Base
from app.models import User, Customer, Supplier, Product
from app.utils import get_password_hash


# 所有需要设置起始 ID 的表
AUTOINCREMENT_TABLES = [
    "users", "customers", "suppliers", "products"
]

# ID 起始值（从 12600000 开始）
ID_START_VALUE = 12599999


def init_base_data():
    """初始化基础数据"""
    print("=" * 50)
    print("开始初始化基础数据...")
    print("=" * 50)

    db = SessionLocal()
    try:
        # 1. 创建所有表
        print("\n[1/4] 创建数据库表...")
        Base.metadata.create_all(bind=engine)
        print("✓ 数据库表创建完成")

        # 2. 创建管理员账号
        print("\n[2/4] 创建管理员账号...")
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

        # 3. 生成基础测试数据
        print("\n[3/4] 生成基础测试数据...")
        generate_base_data(db)
        db.commit()
        print("✓ 测试数据生成完成")

        # 4. 重置自增 ID 起始值
        print("\n[4/4] 重置自增 ID 起始值...")
        for table_name in AUTOINCREMENT_TABLES:
            db.execute(text(f"UPDATE sqlite_sequence SET seq = {ID_START_VALUE} WHERE name = '{table_name}'"))
        db.commit()
        print(f"✓ ID 起始值已重置为 {ID_START_VALUE}")

        print("\n" + "=" * 50)
        print("✓ 基础数据初始化完成！")
        print("=" * 50)
        print("\n数据概览:")
        print(f"  - 客户：8 个")
        print(f"  - 供应商：3 个")
        print(f"  - 商品：10 个")
        print("\n提示：如需生成完整测试数据（含订单、发票），请运行：python init_db.py")

    except Exception as e:
        print(f"\n✗ 初始化失败：{e}")
        db.rollback()
        raise
    finally:
        db.close()


def generate_base_data(db):
    """生成基础测试数据"""

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



if __name__ == "__main__":
    init_base_data()
