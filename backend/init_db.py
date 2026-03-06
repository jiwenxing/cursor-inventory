"""
初始化数据库脚本
创建管理员账号
生成测试数据
"""
from app.database import SessionLocal, engine, Base
from app.models import User, Customer, Supplier, Product, SalesOrder, SalesOrderItem, InventoryRecord, InventorySummary, Invoice, InvoiceItem
from app.utils import get_password_hash
from datetime import datetime, timedelta
import random


def init_db():
    """初始化数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
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

        # 检查是否已有数据
        if db.query(Customer).first():
            print("✓ 数据库已有数据，跳过测试数据生成")
            return

        # 生成测试数据
        generate_test_data(db)

    except Exception as e:
        print(f"✗ 初始化失败：{e}")
        db.rollback()
    finally:
        db.close()


def generate_test_data(db):
    """生成测试数据"""
    print("\n开始生成测试数据...")

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
    print(f"✓ 创建 {len(customers)} 个客户")

    # 2. 创建供应商
    suppliers = [
        Supplier(name="上海电气集团", contact="张经理", phone="021-12345678", email="shanghai@electric.com", address="上海市"),
        Supplier(name="苏州精密机械厂", contact="李工", phone="0512-87654321", email="suzhou@precision.com", address="苏州市"),
        Supplier(name="南京自动化公司", contact="王总", phone="025-11112222", email="nanjing@auto.com", address="南京市"),
    ]
    for s in suppliers:
        db.add(s)
    db.flush()
    print(f"✓ 创建 {len(suppliers)} 个供应商")

    # 3. 创建商品
    products = [
        Product(name="变频器", model="VFD-A", brand="松下", unit="台", tax_rate=0.13, purchase_price=800, retail_price=1200, supplier_id=suppliers[0].id),
        Product(name="PLC控制器", model="PLC-200", brand="西门子", unit="台", tax_rate=0.13, purchase_price=2500, retail_price=3800, supplier_id=suppliers[0].id),
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
    print(f"✓ 创建 {len(products)} 个商品")

    # 创建入库记录（增加库存）
    admin_user = db.query(User).filter(User.username == "admin").first()
    for p in products:
        # 每种商品入库100个
        record = InventoryRecord(
            product_id=p.id,
            type="IN",
            quantity=100,
            related_order_id=None
        )
        db.add(record)

        # 更新库存汇总
        summary = InventorySummary(product_id=p.id, current_stock=100)
        db.add(summary)
    db.flush()
    print(f"✓ 创建库存记录（每种商品100件）")

    # 4. 创建销售订单和发票
    order_data = [
        # 杭州华为科技 - 3个订单，部分已开票
        {"customer": customers[0], "days_ago": 60, "payment_status": "已付款", "items": [(products[0], 5), (products[1], 2)], "discount": 0.05},
        {"customer": customers[0], "days_ago": 30, "payment_status": "部分付款", "items": [(products[2], 3), (products[3], 4)], "discount": 0},
        {"customer": customers[0], "days_ago": 5, "payment_status": "未付款", "items": [(products[4], 6)], "discount": 0.1},

        # 宁波吉利汽车 - 2个订单
        {"customer": customers[1], "days_ago": 45, "payment_status": "已付款", "items": [(products[5], 20), (products[6], 50)], "discount": 0.08},
        {"customer": customers[1], "days_ago": 10, "payment_status": "未付款", "items": [(products[7], 8), (products[8], 15)], "discount": 0},

        # 温州正泰电器 - 2个订单
        {"customer": customers[2], "days_ago": 20, "payment_status": "部分付款", "items": [(products[0], 10), (products[2], 5)], "discount": 0.03},
        {"customer": customers[2], "days_ago": 3, "payment_status": "未付款", "items": [(products[9], 100)], "discount": 0},

        # 绍兴海亮集团 - 1个订单
        {"customer": customers[3], "days_ago": 15, "payment_status": "已付款", "items": [(products[1], 3), (products[3], 2), (products[4], 4)], "discount": 0.1},

        # 金华绿源电动车 - 1个订单
        {"customer": customers[4], "days_ago": 7, "payment_status": "未付款", "items": [(products[5], 30)], "discount": 0.05},
    ]

    invoices_created = []

    for i, data in enumerate(order_data):
        order_date = datetime.now() - timedelta(days=data["days_ago"])

        # 计算订单金额
        total = 0
        order_items = []
        for product, qty in data["items"]:
            final_price = product.retail_price * (1 - data["discount"])
            line_total = qty * final_price
            total += line_total
            order_items.append({
                "product_id": product.id,
                "quantity": qty,
                "unit_price_tax": product.retail_price,
                "discount_rate": data["discount"],
                "final_unit_price_tax": final_price,
                "line_total": line_total,
                "shipped_quantity": 0,
                "unshipped_quantity": qty
            })

        # 创建订单
        order = SalesOrder(
            order_date=order_date,
            customer_id=data["customer"].id,
            salesperson_id=admin_user.id,
            contract_amount=total,
            payment_status=data["payment_status"],
            total_amount=total
        )
        db.add(order)
        db.flush()

        # 创建订单明细
        for item_data in order_items:
            item = SalesOrderItem(order_id=order.id, **item_data)
            db.add(item)

            # 减少库存
            record = InventoryRecord(
                product_id=item_data["product_id"],
                type="OUT",
                quantity=item_data["quantity"],
                related_order_id=order.id
            )
            db.add(record)

        # 更新库存汇总
        for item_data in order_items:
            summary = db.query(InventorySummary).filter(InventorySummary.product_id == item_data["product_id"]).first()
            if summary:
                summary.current_stock -= item_data["quantity"]

        # 根据时间决定是否开票
        if data["days_ago"] >= 20:
            # 创建发票（模拟部分开票或全部开票）
            invoiced_ratio = random.choice([0.5, 0.8, 1.0])  # 50%, 80%, 100% 开票
            invoice_amount = total * invoiced_ratio
            tax_amount = invoice_amount * 0.13

            # 生成发票号
            invoice_no = f"INV{datetime.now().strftime('%Y%m%d')}{i+1:04d}"

            invoice = Invoice(
                invoice_no=invoice_no,
                invoice_date=order_date + timedelta(days=random.randint(1, 5)),
                customer_id=data["customer"].id,
                total_amount=invoice_amount,
                tax_amount=tax_amount,
                status="已开票",
                created_by=admin_user.id
            )
            db.add(invoice)
            db.flush()

            # 创建发票明细
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                order_id=order.id,
                order_no=order.id,
                amount=invoice_amount,
                tax_amount=tax_amount
            )
            db.add(invoice_item)
            invoices_created.append(invoice)

    db.commit()
    print(f"✓ 创建 {len(order_data)} 个销售订单")
    print(f"✓ 创建 {len(invoices_created)} 张发票")
    print("\n✓ 测试数据生成完成！")
    print(f"  - 客户：{len(customers)} 个")
    print(f"  - 供应商：{len(suppliers)} 个")
    print(f"  - 商品：{len(products)} 个")
    print(f"  - 销售订单：{len(order_data)} 个")
    print(f"  - 发票：{len(invoices_created)} 张")


if __name__ == "__main__":
    init_db()
