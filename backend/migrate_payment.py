"""
数据库迁移脚本
添加收款记录相关字段和表：
1. 在 sales_orders 表添加 paid_amount 字段
2. 创建 payment_records 表
"""
from sqlalchemy import text
from app.database import SessionLocal, engine


def migrate():
    """执行数据库迁移"""
    db = SessionLocal()

    try:
        # 1. 在 sales_orders 表添加 paid_amount 字段
        print("正在添加 sales_orders.paid_amount 字段...")
        try:
            db.execute(text(
                "ALTER TABLE sales_orders ADD COLUMN paid_amount FLOAT DEFAULT 0"
            ))
            print("✓ 添加 paid_amount 字段成功")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("✓ paid_amount 字段已存在，跳过")
            else:
                raise e

        # 2. 创建 payment_records 表
        print("正在创建 payment_records 表...")
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS payment_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    payment_date DATETIME NOT NULL,
                    payment_method VARCHAR(20) DEFAULT '银行转账',
                    remark TEXT,
                    created_by INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES sales_orders(id),
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            """))
            print("✓ 创建 payment_records 表成功")
        except Exception as e:
            print(f"创建 payment_records 表失败：{e}")
            raise e

        # 3. 创建索引
        print("正在创建索引...")
        try:
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_payment_order_id ON payment_records(order_id)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_payment_date ON payment_records(payment_date)"))
            print("✓ 创建索引成功")
        except Exception as e:
            print(f"创建索引失败：{e}")

        db.commit()
        print("\n=== 数据库迁移完成 ===")
        print("新增功能:")
        print("- sales_orders 表新增 paid_amount 字段（已付金额）")
        print("- 新增 payment_records 表（收款记录表）")

    except Exception as e:
        db.rollback()
        print(f"\n迁移失败：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
