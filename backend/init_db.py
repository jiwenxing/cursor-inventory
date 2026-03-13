"""
初始化数据库脚本
创建管理员账号
生成基础测试数据：客户、供应商、商品、初始库存
"""
from sqlalchemy import text
from app.database import SessionLocal, engine, Base
from app.models import User, Customer, Supplier, Product, InventoryRecord, InventorySummary
from app.utils import get_password_hash
from datetime import datetime


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
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 先在插入任何数据之前设置所有表的起始 ID
        # 这样可以确保第一次插入时就使用指定的起始值
        for table_name in AUTOINCREMENT_TABLES:
            db.execute(text(f"INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES ('{table_name}', {ID_START_VALUE - 1})"))
        db.commit()

        # 检查是否已有管理员
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

        # 检查是否已有基础数据
        if db.query(Customer).first():
            print("✓ 数据库已有数据，跳过测试数据生成")
            db.commit()
            return

        # 生成基础测试数据
        generate_base_data(db)

        db.commit()

        print(f"✓ 所有表 ID 起始值已设置为 {ID_START_VALUE}")

    except Exception as e:
        print(f"✗ 初始化失败：{e}")
        db.rollback()
    finally:
        db.close()


def generate_base_data(db):
    """生成基础测试数据"""
    print("\n开始生成基础测试数据...")

    now = datetime.now()

    # 1. 使用原生 SQL 插入客户（避免 SQLAlchemy flush 导致 sqlite_sequence 被覆盖）
    customers_data = [
        (ID_START_VALUE, "杭州华为科技有限公司", "张经理", "13800138001", "zhang@huawei.com", "杭州市西湖区"),
        (ID_START_VALUE + 1, "宁波吉利汽车", "李总", "13800138002", "li@geely.com", "宁波市北仑区"),
        (ID_START_VALUE + 2, "温州正泰电器", "王主任", "13800138003", "wang@chint.com", "温州市乐清市"),
        (ID_START_VALUE + 3, "绍兴海亮集团", "刘经理", "13800138004", "liu@hangliang.com", "绍兴市诸暨市"),
        (ID_START_VALUE + 4, "金华绿源电动车", "陈总", "13800138005", "chen@lvyuan.com", "金华市婺城区"),
        (ID_START_VALUE + 5, "台州星星集团", "周经理", "13800138006", "zhou@xingxing.com", "台州市椒江区"),
        (ID_START_VALUE + 6, "嘉兴梦迪集团", "吴总", "13800138007", "wu@mengdi.com", "嘉兴市秀洲区"),
        (ID_START_VALUE + 7, "湖州久盛电气", "郑工", "13800138008", "zheng@jiusheng.com", "湖州市南浔区"),
    ]
    for data in customers_data:
        db.execute(text("""
            INSERT INTO customers (id, name, contact, phone, email, address, created_at)
            VALUES (:id, :name, :contact, :phone, :email, :address, :created_at)
        """), {
            "id": data[0],
            "name": data[1],
            "contact": data[2],
            "phone": data[3],
            "email": data[4],
            "address": data[5],
            "created_at": now
        })
    db.commit()
    print(f"✓ 创建 {len(customers_data)} 个客户")

    # 2. 使用原生 SQL 插入供应商
    suppliers_data = [
        (ID_START_VALUE, "上海电气集团", "张经理", "021-12345678", "shanghai@electric.com", "上海市"),
        (ID_START_VALUE + 1, "苏州精密机械厂", "李工", "0512-87654321", "suzhou@precision.com", "苏州市"),
        (ID_START_VALUE + 2, "南京自动化公司", "王总", "025-11112222", "nanjing@auto.com", "南京市"),
    ]
    for data in suppliers_data:
        db.execute(text("""
            INSERT INTO suppliers (id, name, contact, phone, email, address, created_at)
            VALUES (:id, :name, :contact, :phone, :email, :address, :created_at)
        """), {
            "id": data[0],
            "name": data[1],
            "contact": data[2],
            "phone": data[3],
            "email": data[4],
            "address": data[5],
            "created_at": now
        })
    db.commit()
    print(f"✓ 创建 {len(suppliers_data)} 个供应商")

    # 3. 使用原生 SQL 插入商品
    products_data = [
        (ID_START_VALUE, "变频器", "VFD-A", "松下", "台", 0.13, 800, 1200, suppliers_data[0][0]),
        (ID_START_VALUE + 1, "PLC 控制器", "PLC-200", "西门子", "台", 0.13, 2500, 3800, suppliers_data[0][0]),
        (ID_START_VALUE + 2, "伺服电机", "SM-100", "安川", "台", 0.13, 1500, 2200, suppliers_data[1][0]),
        (ID_START_VALUE + 3, "触摸屏", "HMI-7", "威纶", "台", 0.13, 600, 950, suppliers_data[1][0]),
        (ID_START_VALUE + 4, "减速机", "NMRV-30", "台邦", "台", 0.13, 400, 650, suppliers_data[2][0]),
        (ID_START_VALUE + 5, "传感器", "GZ-001", "倍加福", "个", 0.13, 80, 150, suppliers_data[2][0]),
        (ID_START_VALUE + 6, "继电器", "MY2N", "欧姆龙", "个", 0.13, 15, 28, suppliers_data[0][0]),
        (ID_START_VALUE + 7, "断路器", "NSX-100", "施耐德", "个", 0.13, 350, 520, suppliers_data[1][0]),
        (ID_START_VALUE + 8, "接触器", "LC1D32", "施耐德", "个", 0.13, 120, 190, suppliers_data[1][0]),
        (ID_START_VALUE + 9, "按钮开关", "XB2-EA", "施耐德", "个", 0.13, 8, 15, suppliers_data[2][0]),
    ]
    for data in products_data:
        db.execute(text("""
            INSERT INTO products (id, name, model, brand, unit, tax_rate, purchase_price, retail_price, supplier_id, created_at)
            VALUES (:id, :name, :model, :brand, :unit, :tax_rate, :purchase_price, :retail_price, :supplier_id, :created_at)
        """), {
            "id": data[0],
            "name": data[1],
            "model": data[2],
            "brand": data[3],
            "unit": data[4],
            "tax_rate": data[5],
            "purchase_price": data[6],
            "retail_price": data[7],
            "supplier_id": data[8],
            "created_at": now
        })
    db.commit()
    print(f"✓ 创建 {len(products_data)} 个商品")

    # 4. 创建初始库存记录（初始库存为 0）
    for i, p in enumerate(products_data):
        db.execute(text("""
            INSERT INTO inventory_summary (product_id, current_stock)
            VALUES (:product_id, :current_stock)
        """), {
            "product_id": p[0],
            "current_stock": 0
        })
    db.commit()
    print(f"✓ 创建库存记录（每种商品初始库存为 0）")

    print("\n✓ 基础测试数据生成完成！")
    print(f"  - 客户：{len(customers_data)} 个")
    print(f"  - 供应商：{len(suppliers_data)} 个")
    print(f"  - 商品：{len(products_data)} 个")


if __name__ == "__main__":
    init_db()
