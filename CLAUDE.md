# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在本项目中工作时提供指导。

## 项目概述

适用于10人以内小型销售公司的进销存系统，同时包含简单的进销开票管理功能。后端采用 FastAPI + SQLite，前端采用 Vue3 + ElementPlus。

## 命令

### 本地开发

```bash
# 后端
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 初始化数据库（按顺序执行）
python3 init_db.py              # 1. 创建表和管理员账号
python3 init_test_data.py       # 2. 生成测试数据（客户、供应商、商品）

# 启动服务
uvicorn main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

### 数据库操作

```bash
# 仅重置基础数据（保留订单、发票等）
python3 reset_base_data.py

# 完全重置（删除所有数据重新生成）
rm data/app.db && python3 init_db.py && python3 init_test_data.py
```

### 测试数据

测试数据生成逻辑已集中到 `test_data.py` 模块中，包含：
- `generate_base_data()` - 生成客户、供应商、商品、库存
- `generate_customers()` - 生成客户数据
- `generate_suppliers()` - 生成供应商数据
- `generate_products()` - 生成商品数据
- `generate_initial_inventory()` - 生成初始库存

相关脚本：
- `init_db.py` - 仅创建表和管理员账号（生产初始化）
- `init_test_data.py` - 生成测试数据（客户、供应商、商品）
- `reset_base_data.py` - 重置并生成测试数据（含初始库存）

## 开发规范

### 代码修改原则
- 数据库 Schema 变更后必须同步更新 models.py 和 schemas.py

### 代码风格
- 后端：遵循项目现有的 SQLAlchemy ORM 风格，不引入原生 SQL

### 禁止事项
- 不引入新的重量级依赖（项目定位是简单系统）
- 暂时不修改 JWT 认证逻辑（在 utils.py 中）除非明确要求

## 已知问题 & 注意事项
- SQLite 并发写入有限制，不适合高并发场景（这是设计取舍，勿优化）
- 系统暂时还未上线，数据库 Schema 可能随时变更，但是系统设计要考虑到未来可能的扩展

## 关键业务规则

### 发票管理
- 分为销售发票和进项发票
- 不做复杂的税控系统
- 只做开票记录管理
- 做可开票余额计算
- 做进销匹配分析

### 收款管理
- 支持一笔订单多次收款
- 付款状态自动计算：未付款/部分付款/已付款
- 收款记录表：`payment_records`
- 订单表增加 `paid_amount` 字段记录已付金额
- 删除收款记录时自动重新计算订单付款状态



