"""
修复已有发票数据的脚本
为没有 sales_order_item_invoices 记录的发票补充开票记录
"""
from sqlalchemy import func
from app.database import SessionLocal
from app.models import Invoice, InvoiceItem, SalesOrder, SalesOrderItem, SalesOrderItemInvoice


def fix_invoice_data():
    """修复发票数据"""
    db = SessionLocal()

    try:
        # 获取所有发票
        invoices = db.query(Invoice).all()
        fixed_count = 0

        for invoice in invoices:
            # 检查该发票是否已经有 sales_order_item_invoices 记录
            for invoice_item in invoice.items:
                existing = db.query(SalesOrderItemInvoice).filter(
                    SalesOrderItemInvoice.invoice_item_id == invoice_item.id
                ).first()

                if not existing:
                    # 需要为该发票明细补充开票记录
                    order = db.query(SalesOrder).filter(SalesOrder.id == invoice_item.order_id).first()
                    if not order:
                        continue

                    # 获取订单的所有商品明细
                    order_items = db.query(SalesOrderItem).filter(
                        SalesOrderItem.order_id == invoice_item.order_id
                    ).all()

                    if not order_items:
                        continue

                    order_total = sum(oi.line_total for oi in order_items)

                    if order_total > 0:
                        # 按金额比例分配开票记录
                        for order_item in order_items:
                            ratio = order_item.line_total / order_total
                            invoiced_quantity = order_item.quantity * ratio
                            invoiced_amount = invoice_item.amount * ratio
                            invoiced_tax = invoice_item.tax_amount * ratio

                            db_soi = SalesOrderItemInvoice(
                                order_item_id=order_item.id,
                                invoice_item_id=invoice_item.id,
                                invoiced_quantity=invoiced_quantity,
                                invoiced_amount=invoiced_amount,
                                invoiced_tax_amount=invoiced_tax
                            )
                            db.add(db_soi)
                            fixed_count += 1

        if fixed_count > 0:
            db.commit()
            print(f"修复完成！共补充了 {fixed_count} 条 sales_order_item_invoices 记录")
        else:
            print("所有发票已有完整的开票记录，无需修复")

    except Exception as e:
        db.rollback()
        print(f"修复失败：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix_invoice_data()
