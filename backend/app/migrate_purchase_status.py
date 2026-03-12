"""
迁移脚本：为 purchase_orders 表添加 purchase_status 字段

使用方法：
    cd backend
    source venv/bin/activate
    python app/migrate_purchase_status.py
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

    if "purchase_status" in columns:
        print("✓ purchase_orders 表已包含 purchase_status 列，无需迁移")
    else:
        # 添加 purchase_status 列，默认值为"待下单"
        cursor.execute('''
            ALTER TABLE purchase_orders
            ADD COLUMN purchase_status VARCHAR(20) DEFAULT '待下单'
        ''')
        print("✓ 已为 purchase_orders 表添加 purchase_status 列")

    # 检查 purchase_order_items 表是否还有 purchase_status 列
    cursor.execute("PRAGMA table_info(purchase_order_items)")
    columns = [col[1] for col in cursor.fetchall()]

    if "purchase_status" in columns:
        # SQLite 不支持直接删除列，需要重建表
        print("! 注意：purchase_order_items 表仍包含 purchase_status 列")
        print("  如需删除该列，请手动执行以下操作:")
        print("  1. 备份数据")
        print("  2. 删除 data/app.db")
        print("  3. 重新运行 python3 init_db.py")
    else:
        print("✓ purchase_order_items 表不包含 purchase_status 列")

    conn.commit()
    conn.close()
    print("\n迁移完成!")

if __name__ == "__main__":
    migrate()
