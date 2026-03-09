"""
迁移脚本：添加销售订单和订单明细新字段
- customer_product_code: 客户商品编号
- discounted_price_tax: 含税优惠价
- contract_no: 合同编号
- contract_date: 合同日期
"""

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "data" / "app.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # ==================== 销售订单表 ====================
    cursor.execute("PRAGMA table_info(sales_orders)")
    order_columns = [col[1] for col in cursor.fetchall()]

    # 添加 contract_no 字段
    if "contract_no" not in order_columns:
        cursor.execute(
            "ALTER TABLE sales_orders ADD COLUMN contract_no VARCHAR(100)"
        )
        print("已添加 contract_no 字段")
    else:
        print("contract_no 字段已存在")

    # 添加 contract_date 字段
    if "contract_date" not in order_columns:
        cursor.execute(
            "ALTER TABLE sales_orders ADD COLUMN contract_date TIMESTAMP"
        )
        print("已添加 contract_date 字段")
    else:
        print("contract_date 字段已存在")

    # ==================== 销售订单明细表 ====================
    cursor.execute("PRAGMA table_info(sales_order_items)")
    item_columns = [col[1] for col in cursor.fetchall()]

    # 添加 customer_product_code 字段
    if "customer_product_code" not in item_columns:
        cursor.execute(
            "ALTER TABLE sales_order_items ADD COLUMN customer_product_code VARCHAR(100)"
        )
        print("已添加 customer_product_code 字段")
    else:
        print("customer_product_code 字段已存在")

    # 添加 discounted_price_tax 字段
    if "discounted_price_tax" not in item_columns:
        cursor.execute(
            "ALTER TABLE sales_order_items ADD COLUMN discounted_price_tax FLOAT"
        )
        print("已添加 discounted_price_tax 字段")

        # 将现有的 unit_price_tax 复制到 discounted_price_tax（保持原价作为优惠价）
        cursor.execute(
            "UPDATE sales_order_items SET discounted_price_tax = unit_price_tax WHERE discounted_price_tax IS NULL"
        )
        print("已将现有记录的 unit_price_tax 复制到 discounted_price_tax")
    else:
        print("discounted_price_tax 字段已存在")

    conn.commit()
    print("迁移完成！")

except Exception as e:
    conn.rollback()
    print(f"迁移失败：{e}")
    raise

finally:
    conn.close()
