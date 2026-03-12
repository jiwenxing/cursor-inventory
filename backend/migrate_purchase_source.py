"""
采购订单优化迁移
- 添加来源销售订单字段
- 添加采购状态字段
"""

from app.database import SessionLocal, engine
from sqlalchemy import text


def upgrade(db):
    """升级数据库"""

    # 1. 添加来源销售订单字段
    print("添加 source_sales_order_id 字段...")
    db.execute(text("""
        ALTER TABLE purchase_order_items
        ADD COLUMN source_sales_order_id INTEGER NULL
    """))

    # 2. 添加外键约束（可选，不强制）
    print("添加外键约束...")
    try:
        db.execute(text("""
            ALTER TABLE purchase_order_items
            ADD CONSTRAINT fk_source_sales_order
            FOREIGN KEY (source_sales_order_id) REFERENCES sales_orders(id)
        """))
    except Exception as e:
        print(f"外键约束已存在或创建失败：{e}")

    # 3. 添加采购状态字段
    print("添加 purchase_status 字段...")
    db.execute(text("""
        ALTER TABLE purchase_order_items
        ADD COLUMN purchase_status VARCHAR(20) DEFAULT '待下单'
    """))

    # 4. 更新现有数据：已有入库记录的商品设为"已下单"
    print("更新现有数据状态...")
    db.execute(text("""
        UPDATE purchase_order_items
        SET purchase_status = '已下单'
        WHERE received_quantity > 0
    """))

    db.commit()
    print("迁移完成！")


def downgrade(db):
    """回滚数据库"""

    print("删除 purchase_status 字段...")
    db.execute(text("ALTER TABLE purchase_order_items DROP COLUMN purchase_status"))

    print("删除 source_sales_order_id 字段...")
    db.execute(text("ALTER TABLE purchase_order_items DROP COLUMN source_sales_order_id"))

    db.commit()
    print("回滚完成！")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        print("开始执行数据库迁移...")
        upgrade(db)
        print("迁移成功！")
    except Exception as e:
        db.rollback()
        print(f"迁移失败：{e}")
        raise
    finally:
        db.close()
