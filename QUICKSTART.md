# 快速启动指南

## 前置要求

- Docker 和 Docker Compose（推荐方式）
- 或 Python 3.11+ 和 Node.js 18+（本地开发）

## 方式一：Docker 快速启动（推荐）

### 1. 初始化数据库
```bash
docker-compose --profile init run --rm init-db
```
阿里云ecs命令
```bash
sudo docker compose --profile init run --rm init-db
```

### 2. 启动服务
```bash
docker-compose up -d
```

阿里云ecs命令
```bash
sudo docker compose up -d
```

### 3. 访问系统
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 4. 登录系统
- 用户名: `admin`
- 密码: `admin123`

### 5. 停止服务
```bash
docker-compose down
```

## 方式二：本地开发

### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python init_db.py

# 启动服务
uvicorn main:app --reload --port 8000
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:3000

## 首次使用

1. **登录系统** - 使用默认账号 admin/admin123
2. **添加客户** - 进入"客户管理"，添加客户信息
3. **添加商品** - 进入"商品管理"，添加商品（型号必须唯一）
4. **创建订单** - 进入"销售订单"，创建销售订单
5. **入库操作** - 进入"库存管理"，进行入库操作
6. **查看统计** - 进入"统计报表"，查看销售和应收款统计
7. **导入Excel** - 进入"Excel导入"，导入历史数据

## Excel导入格式

### Sheet1: 销售订单明细
必填字段：
- 订单号
- 订单日期
- 客户（必填）
- 型号（必填）
- 数量（必填）

其他字段：
- 商品名称
- 品牌
- 单价（含税）
- 折扣率
- 金额
- 发货数量
- 合同金额
- 付款状态

### Sheet2: 库存记录
必填字段：
- 型号（必填）
- 库存数量

## 常见问题

### Q: 数据库文件在哪里？
A: `backend/data/app.db`

### Q: 如何备份数据？
A: 直接复制 `backend/data/app.db` 文件

### Q: 如何重置管理员密码？
A: 运行 `python backend/init_db.py` 会重置密码为 admin123

### Q: 端口被占用怎么办？
A: 修改 `docker-compose.yml` 中的端口映射，或修改启动命令中的端口号

### Q: Excel导入失败？
A: 查看导入结果页面的错误详情，根据错误信息修正Excel后重新导入

## 开发调试

### 查看后端日志
```bash
docker-compose logs -f backend
```

### 查看前端日志
```bash
docker-compose logs -f frontend
```

### 进入容器调试
```bash
# 后端容器
docker-compose exec backend bash

# 前端容器
docker-compose exec frontend sh
```

## 生产部署建议

1. 修改 `backend/app/utils.py` 中的 `SECRET_KEY`
2. 修改默认管理员密码
3. 配置HTTPS
4. 定期备份数据库文件
5. 配置日志收集和监控
