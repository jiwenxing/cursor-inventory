# 变更日志

## 2026-03-06

### 新增功能

**供应商管理模块**
- 新增 `suppliers` 表，包含字段：name, contact, phone, email, address, remark
- Product 表添加 `supplier_id` 外键关联 suppliers
- 新增供应商管理页面 `/suppliers`
- 商品管理页面：供应商改为下拉选择框，支持按供应商筛选

**分页功能**
- 商品列表支持分页，默认15条/页
- 支持选择每页显示数量(15/30/50/100)
- 支持跳页

### Bug修复

- 首页商品总数展示异常：商品API改为分页格式后，Dashboard未正确获取total字段
- 分页翻页不生效：handleSearch 函数会重置 currentPage=1，导致翻页后回到第一页

### 界面优化

- 标题改为"杭州松德机械科技有限公司"（原"进销存系统"）
- 标题字体调大至22px
- 移除表格 flex: 1 布局，数据少时不再出现大片空白

### 数据库变更

⚠️ 需要重新初始化数据库：
```bash
rm backend/data/app.db
cd backend && python init_db.py
```

---

## 历史遗留

- 客户管理 customers 表：name, code, contact, phone, address
- 商品管理 products 表：name, model(唯一), brand, unit, tax_rate, purchase_price, retail_price
- 销售订单 sales_orders/sales_order_items
- 库存 inventory_records/inventory_summary