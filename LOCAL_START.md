# 本地启动指南

## 前置要求

- Python 3.11+ 
- Node.js 18+
- pip 和 npm

## 快速启动步骤

### 1. 启动后端

```bash
# 进入backend目录
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

# 初始化数据库（首次运行）
python init_db.py

# 启动后端服务
uvicorn main:app --reload --port 8000
```

后端启动成功后，你会看到：
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. 启动前端（新终端窗口）

```bash
# 进入frontend目录
cd frontend

# 安装依赖（首次运行）
npm install

# 启动前端开发服务器
npm run dev
```

前端启动成功后，你会看到：
```
VITE v5.x.x ready in xxx ms

➜  Local:   http://localhost:3000/
```

### 3. 访问系统

- **前端页面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

### 4. 登录系统

- 用户名: `admin`
- 密码: `admin123`

## 使用启动脚本（更简单）

### macOS/Linux

```bash
# 启动后端
cd backend
chmod +x run.sh
./run.sh

# 启动前端（新终端）
cd frontend
chmod +x run.sh
./run.sh
```

### Windows

```bash
# 启动后端
cd backend
python init_db.py  # 首次运行
uvicorn main:app --reload --port 8000

# 启动前端（新终端）
cd frontend
npm install  # 首次运行
npm run dev
```

## 常见问题

### Q: 端口8000已被占用？
A: 修改启动命令：
```bash
uvicorn main:app --reload --port 8001
```
然后修改 `frontend/vite.config.js` 中的代理端口为8001。

### Q: 端口3000已被占用？
A: Vite会自动选择下一个可用端口，或手动指定：
```bash
npm run dev -- --port 3001
```

### Q: 数据库文件在哪里？
A: `backend/data/app.db`

### Q: 如何重置数据库？
A: 删除 `backend/data/app.db` 文件，然后重新运行 `python init_db.py`

### Q: 模块导入错误？
A: 确保：
1. 在backend目录下运行命令
2. 虚拟环境已激活
3. 所有依赖已安装：`pip install -r requirements.txt`

### Q: npm install 失败？
A: 尝试：
```bash
npm install --legacy-peer-deps
```

### Q: 前端无法连接后端？
A: 检查：
1. 后端是否在8000端口运行
2. `frontend/vite.config.js` 中的代理配置是否正确
3. 浏览器控制台是否有CORS错误

## 开发模式

### 后端热重载
后端使用 `--reload` 参数，代码修改后自动重启。

### 前端热重载
前端使用Vite，代码修改后自动刷新浏览器。

## 停止服务

- 后端：在终端按 `Ctrl+C`
- 前端：在终端按 `Ctrl+C`

## 数据库管理

### 查看数据库
可以使用SQLite工具查看 `backend/data/app.db`：
```bash
sqlite3 backend/data/app.db
```

### 备份数据库
```bash
cp backend/data/app.db backend/data/app.db.backup
```

### 恢复数据库
```bash
cp backend/data/app.db.backup backend/data/app.db
```

## 下一步

1. ✅ 登录系统
2. ✅ 添加客户
3. ✅ 添加商品
4. ✅ 创建销售订单
5. ✅ 进行入库操作
6. ✅ 查看统计报表
7. ✅ 导入Excel数据
