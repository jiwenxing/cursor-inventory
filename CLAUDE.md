# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在本项目中工作时提供指导。

## 项目概述

适用于10人以内小型销售公司的极简进销存系统。后端采用 FastAPI + SQLite，前端采用 Vue3 + ElementPlus。

## 命令

### 本地开发

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_db.py                    # 初始化数据库，默认管理员 (admin/admin123)
uvicorn main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev

# 运行测试
cd backend && pytest tests/test_excel_import.py -v -s
# 或使用: ./backend/run_tests.sh
```

### Docker 部署

```bash
docker-compose --profile init run --rm init-db   # 初始化数据库
docker-compose up -d                              # 启动服务
```

- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 架构

### 后端 (FastAPI + SQLAlchemy + SQLite)

```
backend/
├── main.py              # FastAPI入口，注册所有路由
├── app/
│   ├── api/             # 路由处理器 (auth, customers, products, sales_orders, inventory, import_excel, statistics)
│   ├── models.py         # SQLAlchemy ORM模型 (8张表)
│   ├── schemas.py       # Pydantic 请求/响应模型
│   ├── database.py      # SQLite连接 (存储在 backend/data/app.db)
│   └── utils.py         # JWT认证、密码加密
└── init_db.py           # 数据库初始化脚本
```

### 前端 (Vue3 + Vite + Pinia)

```
frontend/src/
├── views/               # 页面组件 (Login, Dashboard, Customers, Products, SalesOrders, Inventory, Statistics, Import)
├── stores/              # Pinia状态管理 (auth.js)
├── router/              # Vue Router路由配置，含权限守卫
├── api/                 # Axios封装，自动注入Token
├── main.js              # Vue应用入口
└── App.vue              # 主布局 (侧边栏 + 头部)
```

## 数据库表

| 表名 | 用途 |
|------|------|
| users | 用户账户 |
| customers | 客户信息 |
| products | 商品目录 (型号必须唯一) |
| sales_orders | 销售订单主表 |
| sales_order_items | 销售订单明细 |
| inventory_records | 库存流水 (IN/OUT) |
| inventory_summary | 各商品当前库存 |
| import_error_logs | Excel导入错误日志 |

## 关键业务规则

### 库存计算
- 库存通过流水记录计算: `current_stock = SUM(IN) - SUM(OUT)`
- **禁止直接修改 inventory_summary**
- 销售订单自动生成OUT流水
- 入库操作生成IN流水
- 删除订单自动回滚库存

### 金额计算
```
final_unit_price_tax = unit_price_tax × (1 - discount_rate)
line_total = quantity × final_unit_price_tax
order.total_amount = sum(line_total)
```

### Excel导入校验
检测: 库存为负、金额计算错误、发货数量 > 订货数量、型号品牌冲突、合同金额不匹配、必填字段为空

## API路由

- `POST /api/auth/login` - 用户登录
- `GET/POST /api/customers/` - 客户管理
- `GET/POST /api/products/` - 商品管理 (型号唯一)
- `GET/POST /api/sales-orders/` - 销售订单管理
- `GET /api/inventory/summary` - 库存汇总查询
- `POST /api/inventory/in` - 入库操作
- `POST /api/import/excel` - Excel导入(含校验)
- `GET /api/statistics/receivables` - 应收款统计