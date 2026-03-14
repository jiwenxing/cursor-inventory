# 进销存系统

适用于10人以内小型销售公司的极简进销存系统。

## 技术栈

- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: Vue3 + ElementPlus + Vite
- **部署**: Docker + Docker Compose

## 功能特性

### 核心功能
- ✅ 用户登录认证（JWT）
- ✅ 客户管理
- ✅ 供应商管理
- ✅ 商品管理（品牌 + 型号联合唯一）
- ✅ 销售订单录入（支持多商品）
- ✅ 采购订单录入（支持多商品）
- ✅ 入库录入（支持关联采购订单）
- ✅ 库存查询（汇总 + 流水）
- ✅ 销售统计（按客户/商品/时间）
- ✅ 应收款统计
- ✅ Excel导入 + 异常报告

### 业务规则
- 所有库存通过流水自动计算，不允许人工直接修改
- 销售订单保存后自动生成库存OUT流水
- 入库保存后生成库存IN流水
- 自动计算订单金额和行金额
- Excel导入支持异常检测和报告

## 项目结构

```
cursor-inventory/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── models.py        # 数据模型
│   │   ├── schemas.py       # Pydantic模型
│   │   ├── database.py      # 数据库配置
│   │   └── utils.py         # 工具函数
│   ├── data/               # SQLite数据库目录
│   ├── main.py             # FastAPI入口
│   ├── init_db.py          # 初始化数据库脚本
│   └── requirements.txt     # Python依赖
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── stores/         # Pinia状态管理
│   │   ├── router/         # 路由配置
│   │   └── api/            # API调用
│   └── package.json        # Node依赖
├── docker-compose.yml      # Docker编排配置
└── README.md              # 项目文档
```

## 数据库设计

### 核心表结构

**基础数据:**
- `users` - 用户表
- `customers` - 客户表
- `suppliers` - 供应商表
- `products` - 商品表（品牌 + 型号联合唯一）

**采购管理:**
- `purchase_orders` - 采购订单主表
- `purchase_order_items` - 采购订单明细
- `purchase_invoice_items` - 进项发票关联表（预留）

**销售管理:**
- `sales_orders` - 销售订单主表
- `sales_order_items` - 销售订单明细
- `invoices` - 发票主表（销项）
- `invoice_items` - 销项发票关联表

**库存管理:**
- `inventory_records` - 库存流水表
- `inventory_summary` - 库存汇总表

**其他:**
- `import_error_logs` - Excel 导入异常日志

## 快速开始

### 方式一：本地启动（推荐用于开发）

#### 1. 启动后端

```bash
cd backend

# 创建虚拟环境（首次运行）
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库（选择其一）
python init_base_data.py       # 仅基础数据：客户、供应商、商品、库存
python init_db.py              # 完整数据：含销售订单、采购订单、发票

# 启动后端服务
uvicorn main:app --reload --port 8000
```

#### 2. 启动前端（新终端窗口）

```bash
cd frontend

# 安装依赖（首次运行）
npm install

# 启动前端开发服务器
npm run dev
```

#### 3. 访问系统

- **前端页面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

> 💡 详细说明请查看 [LOCAL_START.md](./LOCAL_START.md)

### 方式二：Docker部署（推荐用于生产）

```bash
 # 1. 拉取最新代码
 git pull

 # 2. 重新构建镜像（确保使用最新代码），前端可能不需要
 docker compose build

 # 3. 初始化数据库（如果是全新部署）
 docker compose --profile init run --rm init-db

 # 4. 启动服务
 docker compose up -d

 # 5. 如果需要，执行迁移脚本
 docker compose --profile init run --rm migrate-db

 # 查看服务状态
  docker compose ps
 # 查看日志
 docker compose logs -f
```

3. **访问系统**
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 默认账号

- 用户名: `admin`
- 密码: `admin123`

## Excel导入说明

### Excel格式要求

Excel文件必须包含两个sheet：

**Sheet1: 销售订单明细**
- 订单号
- 订单日期
- 客户
- 商品名称
- 型号（必填）
- 品牌
- 数量（必填）
- 单价（含税）
- 折扣率
- 金额
- 发货数量
- 合同金额
- 付款状态

**Sheet2: 库存记录**
- 型号（必填）
- 库存数量

### 异常检测

系统会自动检测以下异常：
1. 库存为负
2. 金额计算错误（数量 × 单价 × 折扣 ≠ 金额）
3. 发货数量 > 订货数量
4. 相同型号存在多个不同品牌
5. 合同金额 ≠ 订单行金额汇总
6. 关键字段为空（客户/型号/数量）

所有异常会记录到 `import_error_logs` 表，并在导入结果中显示。

## API文档

启动后端后，访问 http://localhost:8000/docs 查看完整的API文档。

### 主要API端点

- `POST /api/auth/login` - 用户登录
- `GET /api/customers/` - 获取客户列表
- `GET /api/products/` - 获取商品列表
- `POST /api/sales-orders/` - 创建销售订单
- `GET /api/inventory/summary` - 获取库存汇总
- `POST /api/inventory/in` - 入库操作
- `POST /api/import/excel` - Excel导入
- `GET /api/statistics/receivables` - 应收款统计

## 开发说明

### 数据库初始化

首次运行前需要初始化数据库，可选择以下脚本：

```bash
# 方式 1：仅基础数据（客户、供应商、商品、库存）
python backend/init_base_data.py

# 方式 2：完整测试数据（含销售订单、采购订单、发票）
python backend/init_db.py
```

两个脚本都会创建数据库表和默认管理员账号（admin/admin123）。

### 数据库重置

```bash
# 仅重置基础数据（保留订单、发票等）
python backend/reset_base_data.py

# 完全重置（删除数据库文件重新生成）
rm backend/data/app.db && python backend/init_db.py
```

### 数据备份

SQLite数据库文件位于 `backend/data/app.db`，定期备份此文件即可。

### 环境变量

生产环境建议修改：
- `SECRET_KEY` (backend/app/utils.py) - JWT密钥
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token过期时间

## 注意事项

1. **型号唯一性**: 商品型号必须唯一，系统会自动检查
2. **库存计算**: 库存通过流水自动计算，不要直接修改 `inventory_summary` 表
3. **订单删除**: 删除订单会自动回滚库存流水
4. **金额精度**: 系统使用2位小数精度，金额计算会自动四舍五入

## 常见问题

### Q: 如何重置管理员密码？
A: 运行 `python backend/init_db.py` 会重置管理员密码为 `admin123`

### Q: 如何备份数据？
A: 直接复制 `backend/data/app.db` 文件即可

### Q: Excel导入失败怎么办？
A: 查看导入结果页面的错误详情，根据错误信息修正Excel后重新导入

## 许可证

MIT License
