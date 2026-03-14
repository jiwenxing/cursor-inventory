from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import pandas as pd
import json
import uuid
from datetime import datetime
from io import BytesIO
import zipfile
import logging
import traceback

logger = logging.getLogger(__name__)
from app.database import get_db
from app.models import (
    User, Customer, Product, SalesOrder, SalesOrderItem,
    InventoryRecord, InventorySummary, ImportErrorLog
)
from app.schemas import ImportResult, ImportErrorLogResponse
from app.utils import get_current_user
from app.timezone import to_cst_datetime
from decimal import Decimal, ROUND_HALF_UP

router = APIRouter()

def normalize_column_name(col_name: str) -> str:
    """标准化列名，去除空格和特殊字符"""
    if pd.isna(col_name):
        return ""
    return str(col_name).strip().replace(" ", "").replace("（", "(").replace("）", ")")

def find_column(df: pd.DataFrame, possible_names: List[str]) -> str:
    """在DataFrame中查找列名（支持多种变体）"""
    normalized_cols = {normalize_column_name(col): col for col in df.columns}

    for name in possible_names:
        normalized_name = normalize_column_name(name)
        if normalized_name in normalized_cols:
            return normalized_cols[normalized_name]

    # 如果找不到，返回第一个可能的名称（用于错误提示）
    return possible_names[0] if possible_names else ""

def round_decimal(value: float, places: int = 2) -> float:
    """四舍五入到指定小数位"""
    if value is None:
        return 0.0
    d = Decimal(str(value))
    return float(d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def detect_errors(row: Dict[str, Any], row_index: int, products_map: Dict[str, Product], customers_map: Dict[str, Customer], col_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """检测单行数据的异常"""
    errors = []

    def get_value(field_name: str, default=None):
        col_name = col_mapping.get(field_name)
        if col_name and col_name in row.index:
            value = row[col_name]
            return value if not pd.isna(value) else default
        return default

    # ① 关键字段为空
    model = str(get_value('model', '')).strip()
    if not model:
        errors.append({
            "error_type": "关键字段为空",
            "error_message": "型号不能为空",
            "row_data": json.dumps(row.to_dict(), ensure_ascii=False, default=str)
        })

    customer = str(get_value('customer', '')).strip()
    if not customer:
        errors.append({
            "error_type": "关键字段为空",
            "error_message": "客户不能为空",
            "row_data": json.dumps(row.to_dict(), ensure_ascii=False, default=str)
        })

    quantity = get_value('quantity', 0)
    if pd.isna(quantity) or float(quantity or 0) <= 0:
        errors.append({
            "error_type": "关键字段为空",
            "error_message": "数量必须大于0",
            "row_data": json.dumps(row.to_dict(), ensure_ascii=False, default=str)
        })

    # ② 金额计算异常
    try:
        quantity_val = float(quantity or 0)
        unit_price = float(get_value('unit_price_tax', 0) or 0)
        discount_rate = float(get_value('discount_rate', 0) or 0)
        amount = float(get_value('amount', 0) or 0)

        if amount > 0:  # 只有当金额字段存在时才检查
            calculated_amount = round_decimal(quantity_val * unit_price * (1 - discount_rate))
            if abs(calculated_amount - amount) > 0.01:  # 允许0.01的误差
                errors.append({
                    "error_type": "金额计算异常",
                    "error_message": f"金额计算错误：数量×单价×折扣={calculated_amount}，实际金额={amount}",
                    "row_data": json.dumps(row.to_dict(), ensure_ascii=False, default=str)
                })
    except (ValueError, TypeError):
        pass  # 如果字段不存在或格式错误，跳过检查

    # ③ 发货数量 > 订货数量
    try:
        shipped_qty = float(get_value('shipped_quantity', 0) or 0)
        order_qty = float(quantity or 0)
        if shipped_qty > order_qty:
            errors.append({
                "error_type": "发货数量异常",
                "error_message": f"发货数量({shipped_qty})大于订货数量({order_qty})",
                "row_data": json.dumps(row.to_dict(), ensure_ascii=False, default=str)
            })
    except (ValueError, TypeError):
        pass

    # ④ 相同型号存在多个不同品牌（在导入时检查）
    brand = str(get_value('brand', '')).strip()
    if model and model in products_map:
        existing_product = products_map[model]
        if existing_product.brand and brand and existing_product.brand != brand:
            errors.append({
                "error_type": "型号品牌冲突",
                "error_message": f"型号{model}已存在，品牌为{existing_product.brand}，当前行为{brand}",
                "row_data": json.dumps(row.to_dict(), ensure_ascii=False, default=str)
            })

    return errors

def detect_order_errors(orders_data: List[Dict[str, Any]], col_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """检测订单级别的异常（合同金额 vs 订单行金额汇总）"""
    errors = []
    order_groups = {}

    def get_value(row: Dict, field_name: str, default=None):
        col_name = col_mapping.get(field_name)
        if col_name and col_name in row:
            value = row[col_name]
            return value if not pd.isna(value) else default
        return default

    # 按订单分组
    for row in orders_data:
        order_no = str(get_value(row, 'order_no', '')).strip()
        order_date = str(get_value(row, 'order_date', ''))
        order_key = f"{order_no}_{order_date}"

        if order_key not in order_groups:
            contract_amount = float(get_value(row, 'contract_amount', 0) or 0)
            order_groups[order_key] = {
                "contract_amount": contract_amount,
                "items": []
            }
        order_groups[order_key]["items"].append(row)

    # 检查每个订单
    for order_key, order_data in order_groups.items():
        contract_amount = order_data["contract_amount"]
        total_line_amount = sum(float(get_value(item, 'amount', 0) or 0) for item in order_data["items"])

        if contract_amount > 0 and abs(contract_amount - total_line_amount) > 0.01:
            errors.append({
                "error_type": "合同金额异常",
                "error_message": f"订单{order_key}：合同金额={contract_amount}，订单行金额汇总={total_line_amount}",
                "row_data": json.dumps(order_data["items"], ensure_ascii=False, default=str)
            })

    return errors

@router.post("/excel", response_model=ImportResult)
async def import_excel(
    file: UploadFile = File(...),
    skip_errors: bool = Query(False, description="是否跳过错误数据继续导入"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导入Excel文件"""
    batch_id = str(uuid.uuid4())
    all_errors = []
    success_count = 0
    error_count = 0

    try:
        # 读取文件内容到BytesIO（确保可以多次读取）
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="上传的文件为空")

        file_bytes = BytesIO(file_content)

        # 优先通过文件头判断文件格式（更可靠）
        file_bytes.seek(0)
        file_header = file_bytes.read(8)
        file_bytes.seek(0)

        # 检测文件格式
        # xlsx格式：前4个字节是 PK\x03\x04 (zip格式)
        # xls格式：前8个字节是 \xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1 (OLE格式)
        is_xlsx = file_header[:2] == b'PK'
        is_xls = file_header[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'

        if is_xlsx:
            engine = 'openpyxl'
            # 验证xlsx文件格式
            try:
                with zipfile.ZipFile(file_bytes, 'r') as zip_file:
                    # 检查是否包含必要的Excel文件结构
                    if 'xl/workbook.xml' not in zip_file.namelist():
                        raise HTTPException(
                            status_code=400,
                            detail="文件格式错误：不是有效的.xlsx文件。请确保文件是使用Excel或兼容软件创建的。"
                        )
            except zipfile.BadZipFile:
                raise HTTPException(
                    status_code=400,
                    detail="文件格式错误：.xlsx文件应该是zip格式。文件可能已损坏或格式不正确。"
                )
            file_bytes.seek(0)
        elif is_xls:
            # 文件头显示是xls格式，但优先尝试openpyxl（因为很多xls文件实际可以用openpyxl读取）
            # 如果openpyxl失败，再尝试xlrd
            engine = 'openpyxl'
            logger.info("文件头检测为xls格式，但优先尝试openpyxl引擎")
        else:
            # 如果文件头无法识别，尝试根据扩展名判断
            filename = file.filename.lower() if file.filename else ''
            if filename.endswith('.xlsx'):
                engine = 'openpyxl'
            elif filename.endswith('.xls'):
                engine = 'xlrd'
            else:
                # 默认尝试openpyxl
                engine = 'openpyxl'

        # 读取Excel
        logger.info(f"开始读取Excel文件: {file.filename}, 使用引擎: {engine}")
        try:
            df_sheet1 = pd.read_excel(file_bytes, sheet_name=0, engine=engine)  # 销售订单明细
            logger.info(f"Sheet1读取成功，行数: {len(df_sheet1)}, 列名: {list(df_sheet1.columns)}")

            # 重置文件指针读取第二个sheet
            file_bytes.seek(0)
            df_sheet2 = pd.read_excel(file_bytes, sheet_name=1, engine=engine)  # 库存记录
            logger.info(f"Sheet2读取成功，行数: {len(df_sheet2)}, 列名: {list(df_sheet2.columns)}")
        except Exception as read_error:
            error_msg = str(read_error)
            logger.error(f"读取Excel文件失败: {error_msg}\n文件: {file.filename}, 引擎: {engine}")
            logger.error(traceback.format_exc())

            # 如果使用openpyxl失败，尝试xlrd（可能是扩展名错误）
            if engine == 'openpyxl':
                logger.info("尝试使用xlrd引擎作为备选...")
                file_bytes.seek(0)
                try:
                    df_sheet1 = pd.read_excel(file_bytes, sheet_name=0, engine='xlrd')
                    file_bytes.seek(0)
                    df_sheet2 = pd.read_excel(file_bytes, sheet_name=1, engine='xlrd')
                    logger.info("✓ 使用xlrd引擎成功读取文件")
                    # 成功使用xlrd读取，继续处理
                except Exception as xlrd_error:
                    logger.error(f"xlrd引擎也失败: {xlrd_error}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"文件格式错误：无法读取Excel文件。\n"
                               f"文件名：{file.filename}\n"
                               f"openpyxl错误：{error_msg}\n"
                               f"xlrd错误：{str(xlrd_error)}\n"
                               f"提示：文件可能已损坏或格式不正确。"
                    )
            elif engine == 'xlrd':
                # 如果使用xlrd失败，尝试openpyxl（文件头可能误判）
                logger.info("尝试使用openpyxl引擎作为备选...")
                file_bytes.seek(0)
                try:
                    df_sheet1 = pd.read_excel(file_bytes, sheet_name=0, engine='openpyxl')
                    file_bytes.seek(0)
                    df_sheet2 = pd.read_excel(file_bytes, sheet_name=1, engine='openpyxl')
                    logger.info("✓ 使用openpyxl引擎成功读取文件")
                    # 成功使用openpyxl读取，继续处理
                except Exception as openpyxl_error:
                    logger.error(f"openpyxl引擎也失败: {openpyxl_error}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"文件格式错误：无法读取Excel文件。\n"
                               f"文件名：{file.filename}\n"
                               f"xlrd错误：{error_msg}\n"
                               f"openpyxl错误：{str(openpyxl_error)}\n"
                               f"提示：文件可能已损坏或格式不正确。请确保文件是有效的.xlsx或.xls格式。"
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"读取Excel文件失败：{error_msg}\n文件名：{file.filename}"
                )

        # 检测并映射列名
        logger.info(f"开始字段映射，Sheet1可用列: {list(df_sheet1.columns)}")
        col_mapping_sheet1 = {
            'order_no': find_column(df_sheet1, ['订单号', '订单编号', 'order_no', 'order_number']),
            'order_date': find_column(df_sheet1, ['订单日期', '日期', 'order_date', 'date']),
            'customer': find_column(df_sheet1, ['客户', '公司', '客户名称', 'customer', 'customer_name']),
            'product_name': find_column(df_sheet1, ['商品名称', '产品名称', 'product_name', 'product']),
            'model': find_column(df_sheet1, ['型号', '产品型号', 'model', 'model_number']),
            'brand': find_column(df_sheet1, ['品牌', 'brand']),
            'quantity': find_column(df_sheet1, ['数量', 'quantity', 'qty']),
            'unit_price_tax': find_column(df_sheet1, ['单价（含税）', '单价(含税)', '含税单价', 'unit_price_tax', 'price']),
            'discount_rate': find_column(df_sheet1, ['折扣率', '折扣', 'discount_rate', 'discount']),
            'amount': find_column(df_sheet1, ['金额', 'amount', 'total']),
            'shipped_quantity': find_column(df_sheet1, ['发货数量', '已发货数量', 'shipped_quantity', 'shipped']),
            'contract_amount': find_column(df_sheet1, ['合同金额', 'contract_amount', 'contract']),
            'payment_status': find_column(df_sheet1, ['付款状态', 'payment_status', 'payment']),
            'unit': find_column(df_sheet1, ['单位', 'unit']),
            'tax_rate': find_column(df_sheet1, ['税率', 'tax_rate', 'tax']),
        }

        logger.info(f"字段映射结果: {col_mapping_sheet1}")

        # 检查必需字段
        required_fields = ['model', 'customer', 'quantity']
        missing_fields = [field for field in required_fields if not col_mapping_sheet1.get(field) or col_mapping_sheet1[field] not in df_sheet1.columns]

        if missing_fields:
            logger.error(f"缺少必需字段: {missing_fields}, 可用列: {list(df_sheet1.columns)}")
            raise HTTPException(
                status_code=400,
                detail=f"Excel文件缺少必需的列：{', '.join(missing_fields)}。\n"
                       f"请确保Sheet1包含以下列：型号、客户（或公司）、数量\n"
                       f"当前Sheet1的列名：{', '.join(df_sheet1.columns.tolist())}"
            )

        # 检测Sheet2的列名
        logger.info(f"开始字段映射Sheet2，可用列: {list(df_sheet2.columns)}")
        col_mapping_sheet2 = {
            'model': find_column(df_sheet2, ['型号', '产品型号', 'model', 'model_number']),
            'stock_quantity': find_column(df_sheet2, ['库存数量', '库存', 'stock_quantity', 'stock', '数量']),
        }

        logger.info(f"Sheet2字段映射结果: {col_mapping_sheet2}")

        if not col_mapping_sheet2.get('model') or col_mapping_sheet2['model'] not in df_sheet2.columns:
            logger.error(f"Sheet2缺少型号列，可用列: {list(df_sheet2.columns)}")
            raise HTTPException(
                status_code=400,
                detail=f"Excel文件Sheet2缺少必需的列：型号\n"
                       f"当前Sheet2的列名：{', '.join(df_sheet2.columns.tolist())}"
            )

        # 先读取所有现有数据
        existing_products = db.query(Product).all()
        products_map = {p.model: p for p in existing_products}

        existing_customers = db.query(Customer).all()
        customers_map = {c.name: c for c in existing_customers}

        # ========== 处理Sheet1：销售订单明细 ==========
        orders_dict = {}  # 按订单号+日期分组

        for idx, row in df_sheet1.iterrows():
            row_errors = detect_errors(row, idx, products_map, customers_map, col_mapping_sheet1)
            if row_errors:
                error_count += 1
                for error in row_errors:
                    error_log = ImportErrorLog(
                        import_batch_id=batch_id,
                        error_type=error["error_type"],
                        error_message=error["error_message"],
                        row_data=error["row_data"]
                    )
                    db.add(error_log)
                    all_errors.append(error)

                if not skip_errors:
                    continue

            # 解析订单信息
            order_date_str = str(row.get("订单日期", ""))
            try:
                if isinstance(row.get("订单日期"), datetime):
                    order_date = row.get("订单日期")
                else:
                    order_date = pd.to_datetime(order_date_str).to_pydatetime()
            except:
                order_date = datetime.now()

            order_key = f"{row.get('订单号', '')}_{order_date}"

            if order_key not in orders_dict:
                customer_name = str(row.get("客户", "")).strip()
                if customer_name not in customers_map:
                    # 创建新客户
                    customer = Customer(name=customer_name)
                    db.add(customer)
                    db.flush()
                    customers_map[customer_name] = customer

                orders_dict[order_key] = {
                    "order_date": order_date,
                    "customer_id": customers_map[customer_name].id,
                    "contract_amount": float(row.get("合同金额", 0) or 0),
                    "payment_status": str(row.get("付款状态", "未付款")).strip() or "未付款",
                    "items": []
                }

            # 解析商品信息
            model = str(row.get("型号", "")).strip()
            if model not in products_map:
                # 创建新商品
                product = Product(
                    name=str(row.get("商品名称", model)).strip(),
                    model=model,
                    brand=str(row.get("品牌", "")).strip() if not pd.isna(row.get("品牌")) else None,
                    unit=str(row.get("单位", "件")).strip() or "件",
                    tax_rate=float(row.get("税率", 0.13) or 0.13)
                )
                db.add(product)
                db.flush()
                products_map[model] = product

            # 添加订单明细
            quantity = float(row.get("数量", 0))
            unit_price_tax = float(row.get("单价（含税）", 0) or 0)
            discount_rate = float(row.get("折扣率", 0) or 0)
            final_price = round_decimal(unit_price_tax * (1 - discount_rate))
            line_total = round_decimal(quantity * final_price)
            shipped_qty = float(row.get("发货数量", 0) or 0)

            orders_dict[order_key]["items"].append({
                "product_id": products_map[model].id,
                "quantity": quantity,
                "unit_price_tax": unit_price_tax,
                "discount_rate": discount_rate,
                "final_unit_price_tax": final_price,
                "line_total": line_total,
                "shipped_quantity": shipped_qty,
                "unshipped_quantity": quantity - shipped_qty
            })

        # 检测订单级别异常
        order_errors = detect_order_errors(df_sheet1.to_dict('records'), col_mapping_sheet1)
        if order_errors:
            error_count += len(order_errors)
            for error in order_errors:
                error_log = ImportErrorLog(
                    import_batch_id=batch_id,
                    error_type=error["error_type"],
                    error_message=error["error_message"],
                    row_data=error["row_data"]
                )
                db.add(error_log)
                all_errors.append(error)

        # 缓存已处理的InventorySummary，避免重复创建
        processed_summaries = {}        # 创建订单
        for order_key, order_data in orders_dict.items():
            if not skip_errors and any(e["error_type"] == "合同金额异常" and order_key in e["error_message"] for e in all_errors):
                continue

            total_amount = sum(item["line_total"] for item in order_data["items"])

            db_order = SalesOrder(
                order_date=order_data["order_date"],
                customer_id=order_data["customer_id"],
                salesperson_id=current_user.id,
                contract_amount=order_data["contract_amount"],
                payment_status=order_data["payment_status"],
                total_amount=total_amount
            )
            db.add(db_order)
            db.flush()
            # 创建订单明细并生成库存流水
            for item_data in order_data["items"]:
                db_item = SalesOrderItem(**item_data, order_id=db_order.id)
                db.add(db_item)

                # 生成库存OUT流水
                inventory_record = InventoryRecord(
                    product_id=item_data["product_id"],
                    type="OUT",
                    quantity=item_data["quantity"],
                    related_order_id=db_order.id
                )
                db.add(inventory_record)

                # 更新库存汇总
                product_id = item_data["product_id"]
                
                # 使用缓存避免重复查询和创建
                if product_id in processed_summaries:
                    summary = processed_summaries[product_id]
                else:
                    summary = db.query(InventorySummary).filter(InventorySummary.product_id == product_id).first()
                    if not summary:
                        summary = InventorySummary(product_id=product_id, current_stock=-item_data["quantity"])
                        db.add(summary)
                    processed_summaries[product_id] = summary
                
                summary.current_stock -= item_data["quantity"]

            success_count += 1

        # 刷新数据库，确保Sheet1中的更改（包括InventorySummary）对Sheet2可见
        db.flush()        # ========== 处理Sheet2：库存记录 ==========
        for idx, row in df_sheet2.iterrows():
            def get_value_sheet2(field_name: str, default=None):
                col_name = col_mapping_sheet2.get(field_name)
                if col_name and col_name in row.index:
                    value = row[col_name]
                    return value if not pd.isna(value) else default
                return default

            model = str(get_value_sheet2('model', '')).strip()
            if not model or model not in products_map:
                error_log = ImportErrorLog(
                    import_batch_id=batch_id,
                    error_type="库存记录异常",
                    error_message=f"型号{model}不存在",
                    row_data=json.dumps(row.to_dict(), ensure_ascii=False, default=str)
                )
                db.add(error_log)
                error_count += 1
                continue

            try:
                stock_qty = float(get_value_sheet2('stock_quantity', 0) or 0)
                if stock_qty < 0:
                    error_log = ImportErrorLog(
                        import_batch_id=batch_id,
                        error_type="库存为负",
                        error_message=f"型号{model}库存数量为负：{stock_qty}",
                        row_data=json.dumps(row.to_dict(), ensure_ascii=False, default=str)
                    )
                    db.add(error_log)
                    error_count += 1
                    if not skip_errors:
                        continue

                product_id = products_map[model].id

                # 获取当前库存，使用缓存避免重复查询
                if product_id in processed_summaries:
                    summary = processed_summaries[product_id]
                else:
                    summary = db.query(InventorySummary).filter(InventorySummary.product_id == product_id).first()
                    if summary:
                        processed_summaries[product_id] = summary
                current_stock = summary.current_stock if summary else 0

                # 计算需要调整的数量
                diff = stock_qty - current_stock

                if abs(diff) > 0.01:
                    # 生成库存调整流水
                    inventory_type = "IN" if diff > 0 else "OUT"
                    inventory_record = InventoryRecord(
                        product_id=product_id,
                        type=inventory_type,
                        quantity=abs(diff),
                        related_order_id=None
                    )
                    db.add(inventory_record)

                    # 更新库存汇总
                    if not summary:
                        summary = InventorySummary(product_id=product_id, current_stock=stock_qty)
                        db.add(summary)
                        processed_summaries[product_id] = summary
                    summary.current_stock = stock_qty

                success_count += 1
            except Exception as e:
                error_log = ImportErrorLog(
                    import_batch_id=batch_id,
                    error_type="库存记录异常",
                    error_message=f"处理失败：{str(e)}",
                    row_data=json.dumps(row.to_dict(), ensure_ascii=False, default=str)
                )
                db.add(error_log)
                error_count += 1

        db.commit()

        # 查询错误日志
        error_logs = db.query(ImportErrorLog).filter(ImportErrorLog.import_batch_id == batch_id).all()
        error_responses = [
            {
                "id": log.id,
                "import_batch_id": log.import_batch_id,
                "error_type": log.error_type,
                "error_message": log.error_message,
                "row_data": log.row_data,
                "created_at": to_cst_datetime(log.created_at)
            }
            for log in error_logs
        ]

        return ImportResult(
            success=error_count == 0 or skip_errors,
            total_rows=len(df_sheet1) + len(df_sheet2),
            success_rows=success_count,
            error_rows=error_count,
            errors=error_responses,
            batch_id=batch_id
        )

    except HTTPException:
        # 重新抛出HTTPException，不记录
        raise
    except Exception as e:
        db.rollback()
        error_detail = str(e)
        error_traceback = traceback.format_exc()
        logger.error(f"Excel导入失败: {error_detail}\n{error_traceback}")
        raise HTTPException(
            status_code=400, 
            detail=f"导入失败：{error_detail}\n\n详细错误信息已记录到日志，请联系管理员查看。"
        )

@router.get("/errors/{batch_id}", response_model=List[ImportErrorLogResponse])
def get_import_errors(batch_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取导入错误日志"""
    errors = db.query(ImportErrorLog).filter(ImportErrorLog.import_batch_id == batch_id).all()
    return [
        {
            "id": error.id,
            "import_batch_id": error.import_batch_id,
            "error_type": error.error_type,
            "error_message": error.error_message,
            "row_data": error.row_data,
            "created_at": to_cst_datetime(error.created_at)
        }
        for error in errors
    ]
