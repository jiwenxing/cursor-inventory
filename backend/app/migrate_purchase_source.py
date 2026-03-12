"""
迁移脚本：为 purchase_orders 表添加 source_sales_order_id 字段

使用方法：
    cd backend
    source venv/bin/activate
    python app/migrate_purchase_source.py
"""

import sqlite3
from pathlib import Path

# 使用相对路径，确保从 backend 目录运行
DB_PATH = Path("data") / "app.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查列是否已存在
    cursor.execute("PRAGMA table_info(purchase_orders)")
    columns = [col[1] for col in cursor.fetchall()]

    if "source_sales_order_id" in columns:
        print("✓ purchase_orders 表已包含 source_sales_order_id 列，无需迁移")
    else:
        # 添加 source_sales_order_id 列
        cursor.execute('''
            ALTER TABLE purchase_orders
            ADD COLUMN source_sales_order_id INTEGER
        ''')
        print("✓ 已为 purchase_orders 表添加 source_sales_order_id 列")

    # 检查 purchase_order_items 表是否还有 source_sales_order_id 列
    cursor.execute("PRAGMA table_info(purchase_order_items)")
    columns = [col[1] for col in cursor.fetchall()]

    if "source_sales_order_id" in columns:
        print("! 注意：purchase_order_items 表仍包含 source_sales_order_id 列")
        print("  该列为旧数据残留，不影响新功能使用")
    else:
        print("✓ purchase_order_items 表不包含 source_sales_order_id 列")

    conn.commit()
    conn.close()
    print("\n迁移完成!")

if __name__ == "__main__":
    migrate()
