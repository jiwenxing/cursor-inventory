-- 进销存系统数据库初始化SQL
-- SQLite数据库建表语句

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- 客户表
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE,
    contact VARCHAR(100),
    phone VARCHAR(50),
    address TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);
CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(code);

-- 商品表
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    model VARCHAR(100) UNIQUE NOT NULL,
    brand VARCHAR(100),
    unit VARCHAR(20) DEFAULT '件',
    tax_rate REAL DEFAULT 0.13,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_model ON products(model);

-- 销售订单主表
CREATE TABLE IF NOT EXISTS sales_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_date DATETIME NOT NULL,
    customer_id INTEGER NOT NULL,
    salesperson_id INTEGER NOT NULL,
    contract_amount REAL DEFAULT 0,
    payment_status VARCHAR(20) DEFAULT '未付款',
    total_amount REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (salesperson_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_sales_orders_date ON sales_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_sales_orders_customer ON sales_orders(customer_id);

-- 销售订单明细表
CREATE TABLE IF NOT EXISTS sales_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit_price_tax REAL NOT NULL,
    discount_rate REAL DEFAULT 0,
    final_unit_price_tax REAL NOT NULL,
    line_total REAL NOT NULL,
    shipped_quantity REAL DEFAULT 0,
    unshipped_quantity REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES sales_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX IF NOT EXISTS idx_sales_order_items_order ON sales_order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_sales_order_items_product ON sales_order_items(product_id);

-- 库存流水表
CREATE TABLE IF NOT EXISTS inventory_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    type VARCHAR(10) NOT NULL,
    quantity REAL NOT NULL,
    related_order_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (related_order_id) REFERENCES sales_orders(id)
);

CREATE INDEX IF NOT EXISTS idx_inventory_records_product ON inventory_records(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_records_date ON inventory_records(created_at);
CREATE INDEX IF NOT EXISTS idx_inventory_records_order ON inventory_records(related_order_id);

-- 库存汇总表
CREATE TABLE IF NOT EXISTS inventory_summary (
    product_id INTEGER PRIMARY KEY,
    current_stock REAL DEFAULT 0 NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 导入异常日志表
CREATE TABLE IF NOT EXISTS import_error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_batch_id VARCHAR(50) NOT NULL,
    error_type VARCHAR(50) NOT NULL,
    error_message TEXT NOT NULL,
    row_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_import_error_logs_batch ON import_error_logs(import_batch_id);

-- 插入默认管理员账号（密码: admin123）
INSERT OR IGNORE INTO users (username, password_hash, name) 
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJqJqJqJq', '管理员');
