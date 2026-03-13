"""
测试数据生成模块

提供统一的测试数据生成函数，供初始化脚本和重置脚本使用。
将测试数据与生产初始化逻辑分离。
"""
from datetime import datetime
from sqlalchemy import text
from app.models import Customer, Supplier, Product, InventoryRecord, InventorySummary


# ID 起始值配置
BASE_DATA_ID_START = 12599999  # 基础数据（客户、供应商、商品）起始值
FULL_DATA_ID_START = 25999999  # 完整数据（含订单、发票）起始值


def generate_customers(db, id_start: int = BASE_DATA_ID_START):
    """生成客户测试数据"""
    now = datetime.now()
    customers_data = [
        (id_start, "杭州华为科技有限公司", "张经理", "13800138001", "zhang@huawei.com", "杭州市西湖区"),
        (id_start + 1, "宁波吉利汽车", "李总", "13800138002", "li@geely.com", "宁波市北仑区"),
        (id_start + 2, "温州正泰电器", "王主任", "13800138003", "wang@chint.com", "温州市乐清市"),
        (id_start + 3, "绍兴海亮集团", "刘经理", "13800138004", "liu@hangliang.com", "绍兴市诸暨市"),
        (id_start + 4, "金华绿源电动车", "陈总", "13800138005", "chen@lvyuan.com", "金华市婺城区"),
        (id_start + 5, "台州星星集团", "周经理", "13800138006", "zhou@xingxing.com", "台州市椒江区"),
        (id_start + 6, "嘉兴梦迪集团", "吴总", "13800138007", "wu@mengdi.com", "嘉兴市秀洲区"),
        (id_start + 7, "湖州久盛电气", "郑工", "13800138008", "zheng@jiusheng.com", "湖州市南浔区"),
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
    return len(customers_data)


def generate_suppliers(db, id_start: int = BASE_DATA_ID_START):
    """生成供应商测试数据"""
    now = datetime.now()
    suppliers_data = [
        (id_start, "上海电气集团", "张经理", "021-12345678", "shanghai@electric.com", "上海市"),
        (id_start + 1, "苏州精密机械厂", "李工", "0512-87654321", "suzhou@precision.com", "苏州市"),
        (id_start + 2, "南京自动化公司", "王总", "025-11112222", "nanjing@auto.com", "南京市"),
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
    return len(suppliers_data)


def generate_products(db, supplier_ids: list, id_start: int = BASE_DATA_ID_START):
    """生成商品测试数据"""
    now = datetime.now()
    products_data = [
        (id_start, "变频器", "VFD-A", "松下", "台", 0.13, 800, 1200, supplier_ids[0]),
        (id_start + 1, "PLC 控制器", "PLC-200", "西门子", "台", 0.13, 2500, 3800, supplier_ids[0]),
        (id_start + 2, "伺服电机", "SM-100", "安川", "台", 0.13, 1500, 2200, supplier_ids[1]),
        (id_start + 3, "触摸屏", "HMI-7", "威纶", "台", 0.13, 600, 950, supplier_ids[1]),
        (id_start + 4, "减速机", "NMRV-30", "台邦", "台", 0.13, 400, 650, supplier_ids[2]),
        (id_start + 5, "传感器", "GZ-001", "倍加福", "个", 0.13, 80, 150, supplier_ids[2]),
        (id_start + 6, "继电器", "MY2N", "欧姆龙", "个", 0.13, 15, 28, supplier_ids[0]),
        (id_start + 7, "断路器", "NSX-100", "施耐德", "个", 0.13, 350, 520, supplier_ids[1]),
        (id_start + 8, "接触器", "LC1D32", "施耐德", "个", 0.13, 120, 190, supplier_ids[1]),
        (id_start + 9, "按钮开关", "XB2-EA", "施耐德", "个", 0.13, 8, 15, supplier_ids[2]),
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
    return len(products_data)


def generate_initial_inventory(db, product_ids: list, initial_stock: int = 0):
    """生成初始库存数据

    Args:
        db: 数据库会话
        product_ids: 商品 ID 列表
        initial_stock: 每种商品的初始库存数量，默认为 0
    """
    for product_id in product_ids:
        # 创建库存汇总记录
        db.execute(text("""
            INSERT INTO inventory_summary (product_id, current_stock)
            VALUES (:product_id, :current_stock)
        """), {
            "product_id": product_id,
            "current_stock": initial_stock
        })

        # 如果初始库存大于 0，创建入库记录
        if initial_stock > 0:
            record = InventoryRecord(
                product_id=product_id,
                type="IN",
                quantity=initial_stock,
                related_order_id=None,
                related_order_type=None
            )
            db.add(record)

    db.commit()


def generate_base_data(db, id_start: int = BASE_DATA_ID_START, initial_stock: int = 0):
    """生成完整的基础测试数据（客户、供应商、商品、库存）

    Args:
        db: 数据库会话
        id_start: ID 起始值
        initial_stock: 每种商品的初始库存数量，默认为 0

    Returns:
        dict: 生成的数据统计
    """
    # 1. 生成客户
    customer_count = generate_customers(db, id_start)

    # 2. 生成供应商
    supplier_count = generate_suppliers(db, id_start)

    # 3. 获取供应商 ID 列表（用于生成商品）
    supplier_ids = [id_start + i for i in range(supplier_count)]

    # 4. 生成商品
    product_count = generate_products(db, supplier_ids, id_start)

    # 5. 获取商品 ID 列表（用于生成库存）
    product_ids = [id_start + i for i in range(product_count)]

    # 6. 生成初始库存
    generate_initial_inventory(db, product_ids, initial_stock)

    return {
        "customers": customer_count,
        "suppliers": supplier_count,
        "products": product_count,
        "initial_stock": initial_stock
    }
