# 项目结构说明

## 目录结构

```
cursor-inventory/
├── backend/                      # 后端代码
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/                  # API路由模块
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # 认证相关API
│   │   │   ├── customers.py     # 客户管理API
│   │   │   ├── products.py      # 商品管理API
│   │   │   ├── sales_orders.py  # 销售订单API
│   │   │   ├── inventory.py     # 库存管理API
│   │   │   ├── import_excel.py  # Excel导入API
│   │   │   └── statistics.py    # 统计报表API
│   │   ├── models.py            # SQLAlchemy数据模型
│   │   ├── schemas.py           # Pydantic数据模式
│   │   ├── database.py          # 数据库配置
│   │   └── utils.py             # 工具函数（JWT、密码加密等）
│   ├── data/                     # SQLite数据库目录（自动创建）
│   │   └── app.db               # SQLite数据库文件
│   ├── main.py                  # FastAPI应用入口
│   ├── init_db.py               # 数据库初始化脚本
│   ├── init_sql.sql             # SQL建表语句（参考）
│   ├── requirements.txt          # Python依赖
│   ├── Dockerfile               # Docker镜像配置
│   ├── run.sh                   # 启动脚本
│   └── .gitignore
│
├── frontend/                     # 前端代码
│   ├── src/
│   │   ├── views/               # 页面组件
│   │   │   ├── Login.vue        # 登录页
│   │   │   ├── Dashboard.vue    # 首页/仪表盘
│   │   │   ├── Customers.vue    # 客户管理
│   │   │   ├── Products.vue     # 商品管理
│   │   │   ├── SalesOrders.vue  # 销售订单
│   │   │   ├── Inventory.vue    # 库存管理
│   │   │   ├── Statistics.vue   # 统计报表
│   │   │   └── Import.vue       # Excel导入
│   │   ├── stores/              # Pinia状态管理
│   │   │   └── auth.js          # 认证状态
│   │   ├── router/              # 路由配置
│   │   │   └── index.js
│   │   ├── api/                 # API调用封装
│   │   │   └── index.js
│   │   ├── App.vue              # 根组件
│   │   ├── main.js              # 应用入口
│   │   └── style.css            # 全局样式
│   ├── index.html               # HTML模板
│   ├── package.json             # Node依赖
│   ├── vite.config.js           # Vite配置
│   ├── Dockerfile               # Docker镜像配置
│   ├── run.sh                   # 启动脚本
│   └── .gitignore
│
├── docker-compose.yml           # Docker编排配置
├── .dockerignore                # Docker忽略文件
├── README.md                    # 项目文档
└── PROJECT_STRUCTURE.md         # 本文件
```

## 核心文件说明

### 后端核心文件

1. **main.py** - FastAPI应用入口，注册所有路由
2. **app/models.py** - 定义8个数据表模型
3. **app/schemas.py** - 定义API请求/响应数据结构
4. **app/database.py** - SQLite数据库连接配置
5. **app/utils.py** - JWT认证、密码加密等工具函数
6. **app/api/sales_orders.py** - 销售订单业务逻辑（含库存流水自动生成）
7. **app/api/import_excel.py** - Excel导入和异常检测逻辑

### 前端核心文件

1. **src/App.vue** - 主布局组件（侧边栏+头部）
2. **src/router/index.js** - 路由配置和权限守卫
3. **src/stores/auth.js** - 用户认证状态管理
4. **src/api/index.js** - Axios封装，自动添加Token
5. **src/views/SalesOrders.vue** - 销售订单录入页面
6. **src/views/Import.vue** - Excel导入页面

## 数据库表结构

1. **users** - 用户表
2. **customers** - 客户表
3. **products** - 商品表（型号唯一）
4. **sales_orders** - 销售订单主表
5. **sales_order_items** - 销售订单明细表
6. **inventory_records** - 库存流水表（IN/OUT）
7. **inventory_summary** - 库存汇总表（自动计算）
8. **import_error_logs** - Excel导入异常日志表

## 关键业务逻辑

### 库存管理
- 库存通过流水自动计算：`current_stock = SUM(IN) - SUM(OUT)`
- 销售订单保存时自动生成OUT流水
- 入库操作生成IN流水
- 不允许直接修改库存数量

### 金额计算
- `final_unit_price_tax = unit_price_tax × (1 - discount_rate)`
- `line_total = quantity × final_unit_price_tax`
- `order.total_amount = sum(line_total)`

### Excel导入异常检测
1. 库存为负
2. 金额计算错误
3. 发货数量 > 订货数量
4. 型号品牌冲突
5. 合同金额 ≠ 订单行金额汇总
6. 关键字段为空

## 启动方式

### Docker方式（推荐）
```bash
docker-compose --profile init run --rm init-db  # 初始化数据库
docker-compose up -d                             # 启动服务
```

### 本地开发
```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_db.py
uvicorn main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

## 默认账号
- 用户名: `admin`
- 密码: `admin123`
