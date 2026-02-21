#!/bin/bash

# 运行Excel导入功能测试

echo "=========================================="
echo "运行Excel导入功能单元测试"
echo "=========================================="

# 确保在backend目录
cd "$(dirname "$0")"

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 运行测试
pytest tests/test_excel_import.py -v -s

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
