# 业务模块优化设计方案

## 背景与目标

### 业务场景
1. 订单驱动：先收到销售订单
2. 按单采购：根据订单及库存制定采购计划，生成采购订单
3. 按明细开票：根据订单明细开票，支持分多次开票
4. 精确到明细：销项发票需要关联到订单明细，支持指定数量开票

### 当前系统问题
1. 发票与订单明细脱节：InvoiceItem 只关联订单，未关联订单明细
2. 库存扣减时机不当：销售订单创建时即扣减库存，应该先接单后发货
3. 缺乏采购建议：无法根据销售订单和库存自动生成采购建议

---

## 优化方案

### 一、发票模块优化

#### 1.1 数据模型变更
- InvoiceItem 新增：order_item_id, quantity
- SalesOrderItem 新增：invoiced_quantity

#### 1.2 可开票余额计算（明细级别）
```
每条明细可开票数量 = 订购数量 - 已开票数量
每条明细可开票金额 = 可开票数量 x 最终单价
订单可开票余额 = 各明细可开票金额之和
```

#### 1.3 开票流程
1. 选择订单
2. 选择明细行
3. 输入开票数量（默认为未开票数量）
4. 系统自动计算金额
5. 生成发票

---

### 二、销售订单优化

#### 2.1 库存扣减时机调整
- 订单创建时：预占库存（reserved_stock）
- 发货时：实际扣减库存（current_stock）
- 取消时：释放预占

#### 2.2 订单状态
- 草稿 -> 已确认 -> 部分发货 -> 已发货 -> 已完成
- 任意状态 -> 已取消

---

### 三、采购模块优化

#### 3.1 采购建议
```
缺货数量 = 订单需求数量 - 当前库存 - 在途采购数量
```

#### 3.2 从销售订单生成采购订单
- 选择一个或多个销售订单
- 系统自动汇总商品及数量
- 生成采购订单草稿

---

## 涉及文件

### 后端
- backend/app/models.py
- backend/app/schemas.py
- backend/app/api/invoices.py
- backend/app/api/sales_orders.py
- backend/app/api/purchase_suggestions.py (新增)
- backend/main.py

### 新增文件
- backend/migrate_business_module.py (数据库迁移脚本)

---

## 实施步骤

- [x] 第一步：模型和 Schema 变更
- [x] 第二步：开票 API 重构
- [x] 第三步：销售订单调整
- [x] 第四步：采购建议功能
- [ ] 第五步：前端适配（待后续）

---

## 验证方案

1. 开票功能测试
   - 创建销售订单（含多条明细）
   - 对订单明细1开票50件（订单明细共100件）
   - 验证：订单明细1的可开票数量变为50件
   - 再次对同一明细开票30件
   - 验证：订单明细1的可开票数量变为20件

2. 采购建议测试
   - 创建销售订单（商品A，数量100）
   - 当前库存商品A为50
   - 验证采购建议显示缺货50件

---

## API 接口

### 发票相关
- GET /api/invoices/orders/{order_id}/invoice-info - 订单开票信息（订单级）
- GET /api/invoices/orders/{order_id}/invoice-detail - 订单开票详情（明细级）

### 销售订单相关
- PUT /api/sales-orders/{order_id}/status - 更新订单状态
- POST /api/sales-orders/{order_id}/ship - 确认发货
- POST /api/sales-orders/{order_id}/confirm - 确认订单
- POST /api/sales-orders/{order_id}/cancel - 取消订单

### 采购建议相关
- GET /api/purchase-suggestions/suggestions - 获取采购建议
- GET /api/purchase-suggestions/order-demand/{order_id} - 订单商品需求
- POST /api/purchase-suggestions/generate-from-orders - 从销售订单生成采购订单
