# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在本项目中工作时提供指导。

## 项目概述

适用于10人以内小型销售公司的极简进销存系统。后端采用 FastAPI + SQLite，前端采用 Vue3 + ElementPlus。

## 命令

### 本地开发

```bash
# 后端
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 初始化数据库（选择其一）
python3 init_base_data.py       # 仅基础数据：客户、供应商、商品、库存
python3 init_db.py              # 完整数据：含销售订单、采购订单、发票

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
rm data/app.db && python3 init_db.py
```

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




