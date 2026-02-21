#!/bin/bash

# 初始化数据库
if [ ! -f "data/app.db" ]; then
    echo "初始化数据库..."
    python init_db.py
fi

# 启动服务
echo "启动FastAPI服务..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
