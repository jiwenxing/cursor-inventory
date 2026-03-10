"""
数据库迁移脚本
添加开票功能相关：
1. 在 invoice_items 表添加 order_item_id 字段（关联具体商品明细）
2. 创建 sales_order_item_invoices 表（记录商品明细开票详情）
"""
from sqlalchemy import text
from app.database import SessionLocal, engine


def migrate():
    """执行数据库迁移"""
    db = SessionLocal()

    try:
        # 1. 在 invoice_items 表添加 order_item_id 字段
        print("正在添加 invoice_items.order_item_id 字段...")
        try:
            db.execute(text(
                "ALTER TABLE invoice_items ADD COLUMN order_item_id INTEGER"
            ))
            print("✓ 添加 order_item_id 字段成功")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("✓ order_item_id 字段已存在，跳过")
            else:
                raise e

        # 2. 创建 sales_order_item_invoices 表（记录商品明细开票详情）
        print("正在创建 sales_order_item_invoices 表...")
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS sales_order_item_invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_item_id INTEGER NOT NULL,
                    invoice_item_id INTEGER NOT NULL,
                    invoiced_quantity REAL NOT NULL,
                    invoiced_amount REAL NOT NULL,
                    invoiced_tax_amount REAL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_item_id) REFERENCES sales_order_items(id),
                    FOREIGN KEY (invoice_item_id) REFERENCES invoice_items(id)
                )
            """))
            print("✓ 创建 sales_order_item_invoices 表成功")
        except Exception as e:
            print(f"创建 sales_order_item_invoices 表失败：{e}")
            raise e

        # 3. 创建索引
        print("正在创建索引...")
        try:
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_soi_order_item_id ON sales_order_item_invoices(order_item_id)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_soi_invoice_item_id ON sales_order_item_invoices(invoice_item_id)"))
            print("✓ 创建索引成功")
        except Exception as e:
            print(f"创建索引失败：{e}")

        db.commit()
        print("\n=== 数据库迁移完成 ===")
        print("新增功能:")
        print("- invoice_items 表新增 order_item_id 字段（关联具体商品明细）")
        print("- 新增 sales_order_item_invoices 表（记录商品明细开票详情）")

    except Exception as e:
        db.rollback()
        print(f"\n迁移失败：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()